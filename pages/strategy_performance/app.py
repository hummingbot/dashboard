import os
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from utils.database_manager import DatabaseManager
from utils.graphs import CandlesGraph
from utils.st_utils import initialize_st_page


initialize_st_page(title="Strategy Performance", icon="🚀")

BULLISH_COLOR = "#61C766"
BEARISH_COLOR = "#FF665A"

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


@st.cache_resource
def get_databases():
    sqlite_files = [db_name for db_name in os.listdir("data") if db_name.endswith(".sqlite")]
    databases_list = [DatabaseManager(db) for db in sqlite_files]
    return {database.db_name: database for database in databases_list}


def download_csv(df: pd.DataFrame, filename: str, key: str):
    csv = df.to_csv(index=False).encode('utf-8')
    return st.download_button(
                label="Press to Download",
                data=csv,
                file_name=f"{filename}.csv",
                mime="text/csv",
                key=key
            )


def show_strategy_summary(summary_df: pd.DataFrame):
    summary = st.data_editor(summary_df,
                             column_config={"PnL Over Time": st.column_config.LineChartColumn("PnL Over Time",
                                                                                              y_min=0,
                                                                                              y_max=5000),
                                            "Examine": st.column_config.CheckboxColumn(required=True)
                                            },
                             use_container_width=True
                             )
    selected_rows = summary[summary.Examine]
    return selected_rows.drop('Examine', axis=1)


def summary_chart(df: pd.DataFrame):
    fig = px.bar(df, x="Trading Pair", y="Realized PnL", color="Exchange")
    fig.update_traces(width=min(1.0, 0.1 * len(strategy_data.strategy_summary)))
    return fig


st.subheader("🔫 Data source")
dbs = get_databases()
db_names = [x.db_name for x in dbs.values()]
select_tab, upload_tab = st.tabs(["Select", "Upload"])
with select_tab:
    if db_names is not None:
        selected_db_name = st.selectbox("Select a database to use:", db_names)
        selected_db = dbs[selected_db_name]
    else:
        st.warning("Ups! No databases were founded. Try uploading one in Upload tab.")
        selected_db = None
with upload_tab:
    uploaded_db = st.file_uploader("Upload your sqlite database", type=["sqlite", "db"])
    if uploaded_db is not None:
        selected_db = DatabaseManager(uploaded_db)
if selected_db is not None:
    strategy_data = selected_db.get_strategy_data()
    if strategy_data.strategy_summary is not None:
        st.divider()
        st.subheader("📝 Strategy summary")
        table_tab, chart_tab = st.tabs(["Table", "Chart"])
        with table_tab:
            selection = show_strategy_summary(strategy_data.strategy_summary)
            selected_exchange = selection["Exchange"].values[0]
            selected_trading_pair = selection["Trading Pair"].values[0]
        with chart_tab:
            summary_chart = summary_chart(strategy_data.strategy_summary)
            st.plotly_chart(summary_chart, use_container_width=True)
        st.subheader("🔍 Examine Trading Pair")
        if not any("Error" in value for key, value in selected_db.status.items() if key != "position_executor"):
            date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
            start_time, end_time = st.select_slider("Select a time range to analyze",
                                                    options=date_array.tolist(),
                                                    value=(date_array[0], date_array[-1]))

            single_market = True
            if single_market:
                single_market_strategy_data = strategy_data.get_single_market_strategy_data(selected_exchange, selected_trading_pair)
                strategy_data_filtered = single_market_strategy_data.get_filtered_strategy_data(start_time, end_time)

                st.divider()
                with st.container():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"🏦 Market")
                    with col2:
                        st.subheader("📋 General stats")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(label="Exchange", value=strategy_data_filtered.exchange.capitalize())
                    with col2:
                        st.metric(label="Trading pair", value=strategy_data_filtered.trading_pair.upper())
                    with col3:
                        st.metric(label='Start date', value=strategy_data_filtered.start_time.strftime("%Y-%m-%d %H:%M"))
                        st.metric(label='End date', value=strategy_data_filtered.end_time.strftime("%Y-%m-%d %H:%M"))
                    with col4:
                        st.metric(label='Duration (Hours)', value=round(strategy_data_filtered.duration_seconds / 3600, 2))
                        st.metric(label='Price change', value=f"{round(strategy_data_filtered.price_change * 100, 2)} %")

                    st.divider()
                    st.subheader("📈 Performance")
                    col131, col132, col133, col134 = st.columns(4)
                    with col131:
                        st.metric(label=f'Net PNL {strategy_data_filtered.quote_asset}',
                                  value=round(strategy_data_filtered.net_pnl_quote, 2))
                        st.metric(label=f'Trade PNL {strategy_data_filtered.quote_asset}',
                                  value=round(strategy_data_filtered.trade_pnl_quote, 2))
                        st.metric(label=f'Fees {strategy_data_filtered.quote_asset}',
                                  value=round(strategy_data_filtered.cum_fees_in_quote, 2))
                    with col132:
                        st.metric(label='Total Trades', value=strategy_data_filtered.total_orders)
                        st.metric(label='Total Buy Trades', value=strategy_data_filtered.total_buy_trades)
                        st.metric(label='Total Sell Trades', value=strategy_data_filtered.total_sell_trades)
                    with col133:
                        st.metric(label='Inventory change in Base asset',
                                  value=round(strategy_data_filtered.inventory_change_base_asset, 4))
                        st.metric(label='Total Buy Trades Amount',
                                  value=round(strategy_data_filtered.total_buy_amount, 2))
                        st.metric(label='Total Sell Trades Amount',
                                  value=round(strategy_data_filtered.total_sell_amount, 2))
                    with col134:
                        st.metric(label='End Price', value=round(strategy_data_filtered.end_price, 4))
                        st.metric(label='Average Buy Price', value=round(strategy_data_filtered.average_buy_price, 4))
                        st.metric(label='Average Sell Price', value=round(strategy_data_filtered.average_sell_price, 4))

                st.divider()
                st.subheader("🕯️ Candlestick")
                if strategy_data_filtered.market_data is not None:
                    with st.expander("Market activity", expanded=True):
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            interval = st.selectbox("Candles Interval:", intervals.keys(), index=2)
                        with col2:
                            rows_per_page = st.number_input("Candles per Page", value=100, min_value=1, max_value=5000)
                        with col3:
                            total_rows = len(strategy_data_filtered.get_market_data_resampled(interval=f"{intervals[interval]}S"))
                            total_pages = math.ceil(total_rows / rows_per_page)
                            if total_pages > 1:
                                selected_page = st.select_slider("Select page", list(range(total_pages)), key="page_slider")
                            else:
                                selected_page = 0
                        start_idx = selected_page * rows_per_page
                        end_idx = start_idx + rows_per_page
                        candles_df = strategy_data_filtered.get_market_data_resampled(interval=f"{intervals[interval]}S").iloc[
                                     start_idx:end_idx]
                        start_time_page = candles_df.index.min()
                        end_time_page = candles_df.index.max()
                        page_data_filtered = single_market_strategy_data.get_filtered_strategy_data(start_time_page, end_time_page)
                        cg = CandlesGraph(candles_df, show_volume=False, extra_rows=2)
                        cg.add_buy_trades(page_data_filtered.buys)
                        cg.add_sell_trades(page_data_filtered.sells)
                        cg.add_pnl(page_data_filtered, row=2)
                        cg.add_base_inventory_change(page_data_filtered, row=3)
                        fig = cg.figure()
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Market data is not available so the candles graph is not going to be rendered. "
                               "Make sure that you are using the latest version of Hummingbot and market data recorder activated.")
                st.divider()
                st.subheader("Tables")
                with st.expander("💵 Trades"):
                    st.write(strategy_data.trade_fill)
                    download_csv(strategy_data.trade_fill, "trade_fill", "download-trades")
                with st.expander("📩 Orders"):
                    st.write(strategy_data.orders)
                    download_csv(strategy_data.orders, "orders", "download-orders")
                with st.expander("⌕ Order Status"):
                    st.write(strategy_data.order_status)
                    download_csv(strategy_data.order_status, "order_status", "download-order-status")
        else:
            st.warning("We are encountering challenges in maintaining continuous analysis of this database.")
            with st.expander("DB Status"):
                status_df = pd.DataFrame([selected_db.status]).transpose().reset_index()
                status_df.columns = ["Attribute", "Value"]
                st.table(status_df)
    else:
        st.warning("We were unable to process this SQLite database.")
        with st.expander("DB Status"):
            status_df = pd.DataFrame([selected_db.status]).transpose().reset_index()
            status_df.columns = ["Attribute", "Value"]
            st.table(status_df)
