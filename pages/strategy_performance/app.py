import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import math
import plotly.express as px
from utils.database_manager import DatabaseManager
from utils.graphs import CandlesGraph
from utils.st_utils import initialize_st_page

initialize_st_page(title="Strategy Performance", icon="🚀")

BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"

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


def style_metric_cards(
    background_color: str = "rgba(255, 255, 255, 0)",
    border_size_px: int = 1,
    border_color: str = "rgba(255, 255, 255, 0.3)",
    border_radius_px: int = 5,
    border_left_color: str = "rgba(255, 255, 255, 0.5)",
    box_shadow: bool = True,
):

    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
        if box_shadow
        else "box-shadow: none !important;"
    )
    st.markdown(
        f"""
        <style>
            div[data-testid="metric-container"] {{
                background-color: {background_color};
                border: {border_size_px}px solid {border_color};
                padding: 5% 5% 5% 10%;
                border-radius: {border_radius_px}px;
                border-left: 0.5rem solid {border_left_color} !important;
                {box_shadow_str}
            }}
        </style>
        """,
        unsafe_allow_html=True,
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
    if len(selected_rows) > 0:
        return selected_rows.drop('Examine', axis=1)
    else:
        return None

def summary_chart(df: pd.DataFrame):
    fig = px.bar(df, x="Trading Pair", y="Realized PnL", color="Exchange")
    fig.update_traces(width=min(1.0, 0.1 * len(strategy_data.strategy_summary)))
    return fig


def pnl_over_time(df: pd.DataFrame):
    df.reset_index(drop=True, inplace=True)
    df_above = df[df['net_realized_pnl'] >= 0]
    df_below = df[df['net_realized_pnl'] < 0]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_above.index, y=df_above["net_realized_pnl"], marker_color=BULLISH_COLOR, showlegend=False))
    fig.add_trace(go.Bar(x=df_below.index, y=df_below["net_realized_pnl"], marker_color=BEARISH_COLOR, showlegend=False))
    fig.update_layout(title=dict(
        text='Cummulative PnL',  # Your title text
        x=0.43,
        y=0.95,
    ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)')
    return fig


def top_n_trades(series, n: int = 8):
    podium = list(range(0, n))
    top_three_profits = series[series >= 0].sort_values(ascending=True)[-n:]
    top_three_losses = series[series < 0].sort_values(ascending=False)[-n:]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Top Profits",
                         y=podium,
                         x=top_three_profits,
                         base=[0, 0, 0, 0],
                         marker_color=BULLISH_COLOR,
                         orientation='h',
                         text=top_three_profits.apply(lambda x: f"{x:.2f}"),
                         textposition="inside",
                         insidetextfont=dict(color='white')))
    fig.add_trace(go.Bar(name="Top Losses",
                         y=podium,
                         x=top_three_losses,
                         marker_color=BEARISH_COLOR,
                         orientation='h',
                         text=top_three_losses.apply(lambda x: f"{x:.2f}"),
                         textposition="inside",
                         insidetextfont=dict(color='white')))
    fig.update_layout(barmode='stack',
                      title=dict(
                          text='Top/Worst Realized PnLs',  # Your title text
                          x=0.5,
                          y=0.95,
                          xanchor="center",
                          yanchor="top"
                      ),
                      xaxis=dict(showgrid=True, gridwidth=0.01, gridcolor="rgba(211, 211, 211, 0.5)"),  # Show vertical grid lines
                      yaxis=dict(showgrid=False),
                      legend=dict(orientation="h",
                                  x=0.5,
                                  y=1.08,
                                  xanchor="center",
                                  yanchor="bottom"))
    fig.update_yaxes(showticklabels=False,
                     showline=False,
                     range=[- n + 6, n + 1])
    return fig


def intraday_performance(df: pd.DataFrame):
    def hr2angle(hr):
        return (hr * 15) % 360

    def hr_str(hr):
        # Normalize hr to be between 1 and 12
        hr_str = str(((hr - 1) % 12) + 1)
        suffix = ' AM' if (hr % 24) < 12 else ' PM'
        return hr_str + suffix

    df["hour"] = df["timestamp"].dt.hour
    profits = df[df["net_realized_pnl"] >= 0]
    losses = df[df["net_realized_pnl"] < 0]
    polar_profits = profits.groupby("hour")["net_realized_pnl"].sum().reset_index()
    polar_losses = losses.groupby("hour")["net_realized_pnl"].sum().reset_index()
    polar_losses["net_realized_pnl"] = abs(polar_losses["net_realized_pnl"])
    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        name="Profits",
        r=polar_profits["net_realized_pnl"],
        theta=polar_profits["hour"] * 15,
        marker_color=BULLISH_COLOR))
    fig.add_trace(go.Barpolar(
        name="Losses",
        r=polar_losses["net_realized_pnl"],
        theta=polar_losses["hour"] * 15,
        marker_color=BEARISH_COLOR))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showline=False,
            ),
            angularaxis=dict(
                rotation=90,
                direction="clockwise",
                tickvals=[hr2angle(hr) for hr in range(24)],
                ticktext=[hr_str(hr) for hr in range(24)],
            ),
            bgcolor='rgba(255, 255, 255, 0)',

        ),
        legend=dict(
            orientation="h",
            x=0.5,
            y=1.08,
            xanchor="center",
            yanchor="bottom"
        ),
        title=dict(
            text='Intraday Performance',
            x=0.5,
            y=0.93,
            xanchor="center",
            yanchor="bottom"
        ),
    )

    return fig


style_metric_cards()
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
            if selection is not None:
                selected_exchange = selection["Exchange"].values[0]
                selected_trading_pair = selection["Trading Pair"].values[0]
        with chart_tab:
            summary_chart = summary_chart(strategy_data.strategy_summary)
            st.plotly_chart(summary_chart, use_container_width=True)
        if selection is None:
            st.info("Choose a trading pair and start analyzing!")
        else:
            st.divider()
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
                    with st.container():
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
                        with col1:
                            st.metric(label=f'Net PNL {strategy_data_filtered.quote_asset}',
                                      value=round(strategy_data_filtered.net_pnl_quote, 2))
                        with col2:
                            st.metric(label='Total Trades', value=strategy_data_filtered.total_orders)
                        with col3:
                            st.metric(label='Accuracy',
                                      value=round(strategy_data_filtered.accuracy, 2))
                        with col4:
                            st.metric(label="Profit Factor",
                                      value=round(strategy_data_filtered.profit_factor, 2))
                        with col5:
                            st.metric(label='Duration (Hours)',
                                      value=round(strategy_data_filtered.duration_seconds / 3600, 2))
                        with col6:
                            st.metric(label='Price change',
                                      value=f"{round(strategy_data_filtered.price_change * 100, 2)} %")
                        with col7:
                            buy_trades_amount = round(strategy_data_filtered.total_buy_amount, 2)
                            avg_buy_price = round(strategy_data_filtered.average_buy_price, 4)
                            st.metric(label="Total Buy Volume",
                                      value=round(buy_trades_amount * avg_buy_price, 2))
                        with col8:
                            sell_trades_amount = round(strategy_data_filtered.total_sell_amount, 2)
                            avg_sell_price = round(strategy_data_filtered.average_sell_price, 4)
                            st.metric(label="Total Sell Volume",
                                      value=round(sell_trades_amount * avg_sell_price, 2))
                        st.plotly_chart(pnl_over_time(strategy_data_filtered.trade_fill), use_container_width=True)

                    st.subheader("💱 Market activity")
                    if "Error" not in selected_db.status["market_data"] and strategy_data_filtered.market_data is not None:
                        with st.expander("Market activity", expanded=True):
                            col1, col2, col3 = st.columns([1, 1, 2])
                            with col1:
                                interval = st.selectbox("Candles Interval:", intervals.keys(), index=2)
                            with col2:
                                rows_per_page = st.number_input("Candles per Page", value=100, min_value=1, max_value=5000)
                            with col3:
                                total_rows = len(
                                    strategy_data_filtered.get_market_data_resampled(interval=f"{intervals[interval]}S"))
                                total_pages = math.ceil(total_rows / rows_per_page)
                                if total_pages > 1:
                                    selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1,
                                                                     key="page_slider")
                                else:
                                    selected_page = 0
                                start_idx = selected_page * rows_per_page
                                end_idx = start_idx + rows_per_page
                                candles_df = strategy_data_filtered.get_market_data_resampled(
                                    interval=f"{intervals[interval]}S").iloc[
                                             start_idx:end_idx]
                                start_time_page = candles_df.index.min()
                                end_time_page = candles_df.index.max()
                                page_data_filtered = single_market_strategy_data.get_filtered_strategy_data(start_time_page,
                                                                                                            end_time_page)
                            col1, col2 = st.columns([5.5, 1.5])
                            with col1:
                                cg = CandlesGraph(candles_df, show_volume=False, extra_rows=2)
                                cg.add_buy_trades(page_data_filtered.buys)
                                cg.add_sell_trades(page_data_filtered.sells)
                                cg.add_pnl(page_data_filtered, row=2)
                                cg.add_quote_inventory_change(page_data_filtered, row=3)
                                fig = cg.figure()
                                st.plotly_chart(fig, use_container_width=True)
                            with col2:
                                st.plotly_chart(intraday_performance(page_data_filtered.trade_fill), use_container_width=True)
                                st.plotly_chart(top_n_trades(page_data_filtered.trade_fill.net_realized_pnl), use_container_width=True)
                    else:
                        st.warning("Market data is not available so the candles graph is not going to be rendered. "
                                   "Make sure that you are using the latest version of Hummingbot and market data recorder activated.")
                    st.divider()
                    st.subheader("📈 Metrics")
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric(label=f'Trade PNL {strategy_data_filtered.quote_asset}',
                                      value=round(strategy_data_filtered.trade_pnl_quote, 2))
                            st.metric(label=f'Fees {strategy_data_filtered.quote_asset}',
                                      value=round(strategy_data_filtered.cum_fees_in_quote, 2))
                        with col2:
                            st.metric(label='Total Buy Trades', value=strategy_data_filtered.total_buy_trades)
                            st.metric(label='Total Sell Trades', value=strategy_data_filtered.total_sell_trades)
                        with col3:
                            st.metric(label='Total Buy Trades Amount',
                                      value=round(strategy_data_filtered.total_buy_amount, 2))
                            st.metric(label='Total Sell Trades Amount',
                                      value=round(strategy_data_filtered.total_sell_amount, 2))
                        with col4:
                            st.metric(label='Average Buy Price', value=round(strategy_data_filtered.average_buy_price, 4))
                            st.metric(label='Average Sell Price', value=round(strategy_data_filtered.average_sell_price, 4))
                        with col5:
                            st.metric(label='Inventory change in Base asset',
                                      value=round(strategy_data_filtered.inventory_change_base_asset, 4))
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
