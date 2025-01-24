import asyncio
import os
import time
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from backend.services.mongodb_client import MongoDBClient
from frontend.st_utils import get_backend_api_client, initialize_st_page


async def gather_candles_dict_by_trading_pair_cached(params_list: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    """
    Gather and cache market data for multiple parameter sets concurrently.
    """
    async def fetch_market_data(params: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch market data asynchronously by running synchronous code in a thread.
        """
        def sync_fetch_market_data():
            backend_api = get_backend_api_client()  # Synchronous call
            candles = backend_api.get_historical_candles(**params)  # Synchronous call
            candles_df = pd.DataFrame(candles)
            candles_df["datetime"] = pd.to_datetime(candles_df.timestamp, unit="s")
            candles_df["trading_pair"] = params["trading_pair"]
            candles_df.set_index("datetime", inplace=True)
            return candles_df

        # Offload synchronous function to a separate thread
        return await asyncio.to_thread(sync_fetch_market_data)

    tasks = [fetch_market_data(params) for params in params_list]
    results = await asyncio.gather(*tasks)

    # Transform results into a dictionary
    candles_dict = {}
    for result in results:
        trading_pair = result['trading_pair'].iloc[0]
        df = result.drop(columns=['trading_pair'])
        candles_dict[trading_pair] = df

    return candles_dict


def create_coint_figure(controller_config, base_candles, quote_candles):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[controller_config["base_trading_pair"], controller_config["quote_trading_pair"]],
        x_title="Time",
        y_title="Price"
    )

    # Add base market candlesticks
    fig.add_trace(
        go.Scatter(
            x=base_candles.index,
            y=base_candles["close"],
            mode="lines",
            name=f"{controller_config['base_trading_pair']} Close"
        ),
        row=1, col=1
    )

    # Add quote market candlesticks
    fig.add_trace(
        go.Scatter(
            x=quote_candles.index,
            y=quote_candles["close"],
            mode="lines",
            name=f"{controller_config['quote_trading_pair']} Close"
        ),
        row=2, col=1
    )

    # Add horizontal lines for the base market
    fig.add_hline(
        y=controller_config["grid_config_base"]["start_price"],
        row=1, col=1,
        line=dict(color="green", width=2)
    )
    fig.add_hline(
        y=controller_config["grid_config_base"]["end_price"],
        row=1, col=1,
        line=dict(color="green", width=2)
    )
    fig.add_hline(
        y=controller_config["grid_config_base"]["limit_price"],
        row=1, col=1,
        line=dict(color="green", dash="dash")
    )

    # Add horizontal lines for the quote market
    fig.add_hline(
        y=controller_config["grid_config_quote"]["start_price"],
        row=2, col=1,
        line=dict(color="red", width=2)
    )
    fig.add_hline(
        y=controller_config["grid_config_quote"]["end_price"],
        row=2, col=1,
        line=dict(color="red", width=2)
    )
    fig.add_hline(
        y=controller_config["grid_config_quote"]["limit_price"],
        row=2, col=1,
        line=dict(color="red", dash="dash")
    )

    # Update layout
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0.1)',
        font={"color": 'white', "size": 12},
        height=400,  # Smaller height for thumbnails
        hovermode="x unified",
        showlegend=False
    )
    return fig


async def main():
    initialize_st_page(title="Stat Arb Deploy", icon="👨‍🏫")

    if "configs_to_deploy" not in st.session_state:
        st.session_state["configs_to_deploy"] = []
    if "selected_index" not in st.session_state:
        st.session_state["selected_index"] = None
    mongo_client = MongoDBClient(username=os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin"),
                                 password=os.getenv("MONGO_INITDB_ROOT_PASSWORD", "admin"),
                                 host=os.getenv("MONGO_HOST", "localhost"),
                                 port=os.getenv("MONGO_PORT", 27017),
                                 database=os.getenv("MONGO_DATABASE", "mongodb"),)
    await mongo_client.connect()
    col1, col2 = st.columns(2)
    with col1:
        days_to_download = st.number_input("Days to download", 14)
    with col2:
        interval = st.selectbox("Interval", ["1m", "3m", "5m", "15m", "30m", "1h", "4h"])

    st.title("Stat Arb Deploy Tool")
    controller_configs_data = await mongo_client.get_controller_config_data()
    extra_info = [controller_config_data["extra_info"] for controller_config_data in controller_configs_data]
    extra_info_df = pd.DataFrame(extra_info)

    st.write("# TODO: Add base and quote pairs in custom_data")
    fig = px.scatter(
        extra_info_df,
        x="coint_value",
        y="rate_difference",
        custom_data=[extra_info_df.index, extra_info_df["base_rate"], extra_info_df["quote_rate"]]
        # Pass specific columns
    )

    # Customize the hover template to include additional information
    fig.update_traces(
        hovertemplate="""
        <b>Index:</b> %{customdata[0]}<br>
        <b>Base Rate:</b> %{customdata[1]}<br>
        <b>Quote Rate:</b> %{customdata[2]}<br>
        <extra></extra>
        """
    )

    st.plotly_chart(fig, use_container_width=True)

    base_trading_pairs = [controller_config["config"]["base_trading_pair"] for controller_config in controller_configs_data]
    quote_trading_pairs = [controller_config["config"]["quote_trading_pair"] for controller_config in controller_configs_data]
    trading_pairs = list(set(base_trading_pairs + quote_trading_pairs))
    params = [
        {
            "connector": "binance_perpetual",
            "trading_pair": trading_pair,
            "interval": interval,
            "start_time": time.time() - 24 * 60 * 60 * days_to_download,
            "end_time": time.time()
        } for trading_pair in trading_pairs]

    with st.spinner("Fetching candles..."):
        if "candles_dict" not in st.session_state:
            st.session_state["candles_dict"] = await gather_candles_dict_by_trading_pair_cached(params)

    # Gallery layout
    st.title("Gallery of Configurations")

    # Display thumbnails
    cols = st.columns(2)  # Adjust the number of columns based on your layout
    controller_configs_data = [controller_config for controller_config in controller_configs_data]
    for i, config_data in enumerate(controller_configs_data):
        config = config_data["config"]
        extra_info = config_data["extra_info"]
        base_candles = st.session_state["candles_dict"][config["base_trading_pair"]]
        quote_candles = st.session_state["candles_dict"][config["quote_trading_pair"]]

        # Create thumbnail figure
        thumbnail_fig = create_coint_figure(config, base_candles, quote_candles)

        # Display thumbnail in a column
        with cols[i % 2]:
            with st.container(border=True):
                st.write(
                        f"Coint Value: {extra_info['coint_value']:.3f} || "
                        f"Rate Difference (Base - Quote):  {extra_info['rate_difference']:.5f}% || "
                        f"Base Beta {extra_info['grid_base']['beta']:.3f} ||"
                        f"Quote Beta: {extra_info['grid_quote']['beta']:.3f} || "
                        f"Base Rate: {extra_info['base_rate']} ||"
                        f"Quote Rate: {extra_info['quote_rate']}")
                st.plotly_chart(thumbnail_fig, use_container_width=True)
                if st.button(f"Select {config['base_trading_pair']} and {config['quote_trading_pair']}", key=f"button_{i}"):
                    st.session_state["selected_index"] = i

    # Display the selected chart in detail
    if st.session_state["selected_index"] is not None:
        st.subheader("Detailed View")
        selected_config_data = controller_configs_data[st.session_state["selected_index"]]
        selected_config = selected_config_data["config"]
        base_candles = st.session_state["candles_dict"][selected_config["base_trading_pair"]]
        quote_candles = st.session_state["candles_dict"][selected_config["quote_trading_pair"]]

        # Create detailed figure
        detailed_fig = create_coint_figure(selected_config, base_candles, quote_candles)
        detailed_fig.update_layout(height=800)  # Larger height for detailed view
        st.plotly_chart(detailed_fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_amount_quote = st.number_input("Total Amount Quote", value=round(1000.0, 4), format="%.4f")
            leverage = st.number_input("Leverage", value=round(50.0, 4), format="%.4f")
        with col2:
            min_spread_between_orders = st.number_input("Min Spread Between Orders %", value=round(0.02, 4),
                                                        format="%.4f")
            stop_loss = st.number_input("Stop Loss", value=round(0.1, 4), format="%.4f")
        with col3:
            take_profit = st.number_input("Take Profit", value=round(0.0008, 4), format="%.4f")
            time_limit = st.number_input("Time Limit", value=round(259200, 4), format="%.4f")
        with col4:
            activation_price = st.number_input("Activation Price", value=round(0.03, 4), format="%.4f")
            trailing_delta = st.number_input("Trailing Delta", value=round(0.005, 4), format="%.4f")

        selected_config["total_amount_quote"] = total_amount_quote
        selected_config["leverage"] = leverage
        selected_config["'min_spread_between_orders'"] = min_spread_between_orders / 100
        selected_config["triple_barrier_config"] = {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'time_limit': time_limit,
            'trailing_stop': {'activation_price': activation_price, 'trailing_delta': trailing_delta}
        }
        if st.button("Add config"):
            st.session_state["configs_to_deploy"].append(selected_config)
        st.title("Configs to deploy")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.json(st.session_state["configs_to_deploy"])
        with col2:
            st.write("# TODO: Represent configs by id")
            st.write("# TODO: Add version and replace id")
            st.write("# TODO: Add controller configs to Backend API")
            st.write("# TODO: Deploy script with controllers")

if __name__ == "__main__":
    asyncio.run(main())
