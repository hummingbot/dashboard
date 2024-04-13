import pandas as pd
import streamlit as st
import math
from utils.os_utils import get_local_dbs
from utils.sqlite_manager import SQLiteManager
from data_viz.charts import ChartsBase
from data_viz.candles import PerformanceCandles
import data_viz.utils as utils
from utils.st_utils import initialize_st_page, download_csv_button, db_error_message


initialize_st_page(title="Strategy Performance V1", icon="🚀")


# Start content here
intervals = {
    "1m": 60,
    "3m": 60 * 3,
    "5m": 60 * 5,
    "15m": 60 * 15,
    "30m": 60 * 30,
    "1h": 60 * 60,
    "6h": 60 * 60 * 6,
    "1d": 60 * 60 * 24,
}

# Data source section
st.subheader("🔫 Data source")

# Find and select existing databases
dbs = get_local_dbs()
if dbs is not None and bool(dbs):
    bots_source = st.selectbox("Choose a folder containing local databases", dbs.keys())
    db_names = [x for x in dbs[bots_source]]
    selected_db_name = st.selectbox("Select a database", db_names)
    selected_db = SQLiteManager(dbs[bots_source][selected_db_name])
else:
    st.warning("Ups! No databases were founded. Start uploading one in ETL page.")
    selected_db = None
    st.stop()

# Load strategy data
try:
    strategy_data = selected_db.get_strategy_v1_data()
except NotImplementedError as e:
    st.error(f"Error: {e}")
    st.stop()
strategy_version = selected_db.version
charts = ChartsBase()

# Strategy summary section
st.divider()
st.subheader("📝 Strategy summary")
if strategy_data.trade_fill_summary is None:
    db_error_message(db=selected_db,
                     error_message="Inaccesible summary table. Please try uploading a new database.")
    st.stop()
else:
    main_tab, chart_tab = st.tabs(["Main", "Chart"])
    with chart_tab:
        st.plotly_chart(charts.realized_pnl_over_trading_pair(data=strategy_data.trade_fill_summary,
                                                              trading_pair_column="Trading Pair",
                                                              realized_pnl_column="Realized PnL",
                                                              exchange="Exchange"),
                        use_container_width=True)
    with main_tab:
        summary = st.data_editor(strategy_data.trade_fill_summary,
                                 column_config={"PnL Over Time": st.column_config.LineChartColumn("PnL Over Time",
                                                                                                  y_min=0,
                                                                                                  y_max=5000),
                                                "Explore": st.column_config.CheckboxColumn(required=True)
                                                },
                                 use_container_width=True,
                                 hide_index=True
                                 )
        selection = summary[summary.Explore] if not summary[summary.Explore].empty else None
        if selection is None:
            st.info("💡 Choose a trading pair and start analyzing!")
            st.stop()
        elif len(selection) > 1:
            st.warning("This version doesn't support multiple selections. Please try selecting only one.")
            st.stop()
        else:
            selected_exchange = selection["Exchange"].values[0]
            selected_trading_pair = selection["Trading Pair"].values[0]

# Explore Trading Pair section
st.divider()
st.subheader("🔍 Explore Trading Pair")

if any("Error" in status for status in [selected_db.status["trade_fill"], selected_db.status["orders"]]):
    db_error_message(db=selected_db,
                     error_message="Database error. Check the status of your database.")
    st.stop()

# Filter strategy data by time
date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
start_time, end_time = st.select_slider("Select a time range to analyze",
                                        options=date_array.tolist(),
                                        value=(date_array[0], date_array[-1]))
single_market_strategy_data = strategy_data.get_single_market_strategy_data(selected_exchange, selected_trading_pair)
time_filtered_strategy_data = single_market_strategy_data.get_filtered_strategy_data(start_time, end_time)

# Header metrics
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col1:
    st.metric(label=f'Net PNL {time_filtered_strategy_data.quote_asset}',
              value=round(time_filtered_strategy_data.net_pnl_quote, 2),
              help="The overall profit or loss achieved in quote asset.")
with col2:
    st.metric(label='Total Trades', value=time_filtered_strategy_data.total_orders,
              help="The total number of closed trades, winning and losing.")
with col3:
    st.metric(label='Accuracy',
              value=f"{100 * time_filtered_strategy_data.accuracy:.2f} %",
              help="The percentage of winning trades, the number of winning trades divided by the total number of closed trades.")
with col4:
    st.metric(label="Profit Factor",
              value=round(time_filtered_strategy_data.profit_factor, 2),
              help="The amount of money the strategy made for every unit of money it lost, net profits divided by gross losses.")
with col5:
    st.metric(label='Duration (Days)',
              value=round(time_filtered_strategy_data.duration_seconds / (60 * 60 * 24), 2),
              help="The number of days the strategy was running.")
with col6:
    st.metric(label='Price change',
              value=f"{round(time_filtered_strategy_data.price_change * 100, 2)} %",
              help="The percentage change in price from the start to the end of the strategy.")
with col7:
    buy_trades_amount = round(time_filtered_strategy_data.total_buy_amount, 2)
    avg_buy_price = round(time_filtered_strategy_data.average_buy_price, 4)
    st.metric(label="Total Buy Volume",
              value=round(buy_trades_amount * avg_buy_price, 2),
              help="The total amount of quote asset bought.")
with col8:
    sell_trades_amount = round(time_filtered_strategy_data.total_sell_amount, 2)
    avg_sell_price = round(time_filtered_strategy_data.average_sell_price, 4)
    st.metric(label="Total Sell Volume",
              value=round(sell_trades_amount * avg_sell_price, 2),
              help="The total amount of quote asset sold.")

# Cummulative pnl chart
st.plotly_chart(charts.realized_pnl_over_time(data=time_filtered_strategy_data.trade_fill
                                              .sort_values(by="timestamp"),
                                              cum_realized_pnl_column="net_realized_pnl"),
                use_container_width=True)

# Market activity section
st.subheader("💱 Market activity")
if "Error" in selected_db.status["market_data"] or time_filtered_strategy_data.market_data.empty:
    st.warning("Market data is not available so the candles graph is not going to be rendered."
               "Make sure that you are using the latest version of Hummingbot and market data recorder activated.")
else:
    # Visibility options
    with st.expander("Visual Options"):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            show_buys = st.checkbox("Buys", value=False)
        with col2:
            show_sells = st.checkbox("Sells", value=False)
        with col3:
            show_annotations = st.checkbox("Annotations", value=False)
        with col4:
            show_pnl = st.checkbox("PNL", value=True)
        with col5:
            show_quote_inventory_change = st.checkbox("Quote Inventory Change", value=True)
        with col6:
            show_indicators = st.checkbox("Indicators", value=False)
        with col7:
            main_height = st.slider("Main Row Height", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("### Candles config")
        # Set custom configs
        if show_indicators:
            indicators_config_path = st.selectbox("Indicators path", utils.get_indicators_config_paths())
        else:
            indicators_config_path = None
        interval = st.selectbox("Candles Interval:", intervals.keys(), index=2)
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)

        # Add pagination
        total_rows = len(time_filtered_strategy_data.get_market_data_resampled(interval=f"{intervals[interval]}S"))
        total_pages = math.ceil(total_rows / rows_per_page)
        if total_pages > 1:
            selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1, key="page_slider")
        else:
            selected_page = 0
        start_idx = selected_page * rows_per_page
        end_idx = start_idx + rows_per_page
        candles_df = time_filtered_strategy_data.get_market_data_resampled(
            interval=f"{intervals[interval]}S").iloc[start_idx:end_idx]
        start_time_page = candles_df.index.min()
        end_time_page = candles_df.index.max()

        # Get Page Filtered Strategy Data
        page_filtered_strategy_data = single_market_strategy_data.get_filtered_strategy_data(start_time_page, end_time_page)

        # Show auxiliary charts
        intraday_tab, returns_tab, returns_data_tab, other_metrics_tab = st.tabs(["Intraday", "Returns", "Returns Data", "Other Metrics"])
        with intraday_tab:
            st.plotly_chart(charts.intraday_performance(data=page_filtered_strategy_data.trade_fill,
                                                        quote_volume_column="quote_volume",
                                                        datetime_column="timestamp",
                                                        realized_pnl_column="realized_pnl"),
                            use_container_width=True)
        with returns_tab:
            st.plotly_chart(charts.returns_distribution(data=page_filtered_strategy_data.trade_fill,
                                                        realized_pnl_column="realized_pnl"),
                            use_container_width=True)
        with returns_data_tab:
            raw_returns_data = time_filtered_strategy_data.trade_fill[["timestamp", "gross_pnl", "trade_fee", "realized_pnl"]].dropna(subset="realized_pnl")
            st.dataframe(raw_returns_data,
                         use_container_width=True,
                         hide_index=True,
                         height=(min(len(time_filtered_strategy_data.trade_fill) * 39, 600)))
            download_csv_button(raw_returns_data, "raw_returns_data", "download-raw-returns")
        with other_metrics_tab:
            col3, col4 = st.columns(2)
            with col3:
                st.metric(label=f'Trade PNL {time_filtered_strategy_data.quote_asset}',
                          value=round(time_filtered_strategy_data.trade_pnl_quote, 2),
                          help="The overall profit or loss achieved in quote asset, without fees.")
                st.metric(label='Total Buy Trades', value=time_filtered_strategy_data.total_buy_trades,
                          help="The total number of buy trades.")
                st.metric(label='Total Buy Trades Amount',
                          value=round(time_filtered_strategy_data.total_buy_amount, 2),
                          help="The total amount of base asset bought.")
                st.metric(label='Average Buy Price', value=round(time_filtered_strategy_data.average_buy_price, 4),
                          help="The average price of the base asset bought.")

            with col4:
                st.metric(label=f'Fees {time_filtered_strategy_data.quote_asset}',
                          value=round(time_filtered_strategy_data.cum_fees_in_quote, 2),
                          help="The overall fees paid in quote asset.")
                st.metric(label='Total Sell Trades', value=time_filtered_strategy_data.total_sell_trades,
                          help="The total number of sell trades.")
                st.metric(label='Total Sell Trades Amount',
                          value=round(time_filtered_strategy_data.total_sell_amount, 2),
                          help="The total amount of base asset sold.")
                st.metric(label='Average Sell Price', value=round(time_filtered_strategy_data.average_sell_price, 4),
                          help="The average price of the base asset sold.")
    with col1:
        page_candles = PerformanceCandles(trade_fill=page_filtered_strategy_data.trade_fill,
                                          indicators_config=utils.load_indicators_config(indicators_config_path) if show_indicators else None,
                                          candles_df=candles_df,
                                          show_buys=show_buys,
                                          show_sells=show_sells,
                                          show_pnl=show_pnl,
                                          show_quote_inventory_change=show_quote_inventory_change,
                                          show_indicators=show_indicators,
                                          main_height=main_height,
                                          strategy_version=strategy_version,
                                          show_annotations=show_annotations)
        st.plotly_chart(page_candles.figure(), use_container_width=True)

# Tables section
st.divider()
st.subheader("Tables")
with st.expander("💵 Trades"):
    st.write(strategy_data.trade_fill)
    download_csv_button(strategy_data.trade_fill, "trade_fill", "download-trades")
with st.expander("📩 Orders"):
    st.write(strategy_data.orders)
    download_csv_button(strategy_data.orders, "orders", "download-orders")
with st.expander("⌕ Order Status"):
    st.write(strategy_data.order_status)
    download_csv_button(strategy_data.order_status, "order_status", "download-order-status")
if not strategy_data.market_data.empty:
    with st.expander("💱 Market Data"):
        st.write(strategy_data.market_data)
        download_csv_button(strategy_data.market_data, "market_data", "download-market-data")
