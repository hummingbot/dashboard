import os
import pandas as pd
import streamlit as st
from pathlib import Path

from utils.database_manager import DatabaseManager
from utils.graphs import CandlesGraph

title = "Strategy Performance"
icon = "🚀"

st.set_page_config(
    page_title=title,
    page_icon=icon,
    layout="wide",
)
st.title(f"{icon} {title}")

current_directory = Path(__file__).parent
readme_path = current_directory / "README.md"
with st.expander("About This Page"):
    st.write(readme_path.read_text())

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
def get_database(db_name: str):
    db_manager = DatabaseManager(db_name)
    return db_manager


with st.container():
    col1, col2 = st.columns(2)
    with col1:
        db_names = [db_name for db_name in os.listdir("data") if db_name.endswith(".sqlite")]
        selected_db_name = st.selectbox("Select a database to use:",
                                        db_names if len(db_names) > 0 else ["No databases found"])
    if selected_db_name == "No databases found":
        st.warning("No databases available to analyze. Please run a backtesting first.")
    else:
        db_manager = get_database(selected_db_name)
        config_files = db_manager.get_config_files()
        if config_files == []:
            with col1:
                st.warning('No trades have been recorded in the selected database')
        with col2:
            selected_config_file = st.selectbox("Select a config file to analyze:", config_files)
            if selected_config_file is not None:
                exchanges_trading_pairs = db_manager.get_exchanges_trading_pairs_by_config_file(selected_config_file)
                strategy_data = db_manager.get_strategy_data(selected_config_file)
                
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_exchange = st.selectbox("Select an exchange:", [] if selected_config_file is None else list(exchanges_trading_pairs.keys()))
            with col2:
                selected_trading_pair = st.selectbox("Select a trading pair:", [] if selected_config_file is None else exchanges_trading_pairs[selected_exchange])
            with col3:
                interval = st.selectbox("Candles Interval:", intervals.keys(), index=2)

        if selected_exchange and selected_trading_pair:
            single_market_strategy_data = strategy_data.get_single_market_strategy_data(selected_exchange,
                                                                                        selected_trading_pair)
            date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
            start_time, end_time = st.select_slider("Select a time range to analyze", options=date_array.tolist(),
                                                    value=(date_array[0], date_array[-1]))

            strategy_data_filtered = single_market_strategy_data.get_filtered_strategy_data(start_time, end_time)
            row = st.container()
            col11, col12, col13 = st.columns([1, 2, 3])
            with row:
                with col11:
                    st.header(f"🏦 Market")
                    st.metric(label="Exchange", value=strategy_data_filtered.exchange.capitalize())
                    st.metric(label="Trading pair", value=strategy_data_filtered.trading_pair.upper())
                with col12:
                    st.header("📋 General stats")
                    col121, col122 = st.columns(2)
                    with col121:
                        st.metric(label='Duration (Hours)', value=round(strategy_data_filtered.duration_seconds / 3600, 2))
                        st.metric(label='Start date', value=strategy_data_filtered.start_time.strftime("%Y-%m-%d %H:%M"))
                        st.metric(label='End date', value=strategy_data_filtered.end_time.strftime("%Y-%m-%d %H:%M"))
                    with col122:
                        st.metric(label='Price change', value=f"{round(strategy_data_filtered.price_change * 100, 2)} %")
                with col13:
                    st.header("📈 Performance")
                    col131, col132, col133, col134 = st.columns(4)
                    with col131:
                        st.metric(label=f'Net PNL {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.net_pnl_quote, 2))
                        st.metric(label=f'Trade PNL {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.trade_pnl_quote, 2))
                        st.metric(label=f'Fees {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.cum_fees_in_quote, 2))
                    with col132:
                        st.metric(label='Total Trades', value=strategy_data_filtered.total_orders)
                        st.metric(label='Total Buy Trades', value=strategy_data_filtered.total_buy_trades)
                        st.metric(label='Total Sell Trades', value=strategy_data_filtered.total_sell_trades)
                    with col133:
                        st.metric(label='Inventory change in Base asset',
                                  value=round(strategy_data_filtered.inventory_change_base_asset, 4))
                        st.metric(label='Total Buy Trades Amount', value=round(strategy_data_filtered.total_buy_amount, 2))
                        st.metric(label='Total Sell Trades Amount', value=round(strategy_data_filtered.total_sell_amount, 2))
                    with col134:
                        st.metric(label='End Price', value=round(strategy_data_filtered.end_price, 4))
                        st.metric(label='Average Buy Price', value=round(strategy_data_filtered.average_buy_price, 4))
                        st.metric(label='Average Sell Price', value=round(strategy_data_filtered.average_sell_price, 4))
            if strategy_data_filtered.market_data is not None:
                candles_df = strategy_data_filtered.get_market_data_resampled(interval=f"{intervals[interval]}S")
                cg = CandlesGraph(candles_df, show_volume=False, extra_rows=2)
                cg.add_buy_trades(strategy_data_filtered.buys)
                cg.add_sell_trades(strategy_data_filtered.sells)
                cg.add_pnl(strategy_data_filtered, row=2)
                cg.add_base_inventory_change(strategy_data_filtered, row=3)
                fig = cg.figure()
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Market data is not available so the candles graph is not going to be rendered. "
                           "Make sure that you are using the latest version of Hummingbot and market data recorder activated.")

            st.subheader("💵Trades")
            st.write(strategy_data_filtered.trade_fill)

            st.subheader("📩 Orders")
            st.write(strategy_data_filtered.orders)

            st.subheader("⌕ Order Status")
            st.write(strategy_data_filtered.order_status)
