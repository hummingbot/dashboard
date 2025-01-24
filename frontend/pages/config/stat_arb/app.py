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


async def main():
    # Initialize the Streamlit page
    initialize_st_page(title="Stat Arb Deploy", icon="👨‍🏫")
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

    results = []
    base_trading_pairs = [controller_config["config"]["base_trading_pair"] for controller_config in controller_configs_data]
    quote_trading_pairs = [controller_config["config"]["quote_trading_pair"] for controller_config in controller_configs_data]
    trading_pairs = list(set(base_trading_pairs + quote_trading_pairs))
    controller_config_data_selected = st.selectbox("Controller Config Data", options=range(0, len(controller_configs_data)))
    controller_config_data = controller_configs_data[controller_config_data_selected]
    extra_info = controller_config_data["extra_info"]
    controller_config = controller_config_data["config"]
    params = [
        {
            "connector": controller_config["connector_name"],
            "trading_pair": trading_pair,
            "interval": interval,
            "start_time": time.time() - 24 * 60 * 60 * days_to_download,
            "end_time": time.time()
        } for trading_pair in trading_pairs]

    with st.spinner("Fetching candles..."):
        if "candles_dict" not in st.session_state:
            st.session_state["candles_dict"] = await gather_candles_dict_by_trading_pair_cached(params)

    base_candles = st.session_state["candles_dict"][controller_config["base_trading_pair"]]
    quote_candles = st.session_state["candles_dict"][controller_config["quote_trading_pair"]]
    results.append({
        "controller_config": controller_config,
        "extra_info": extra_info,
        "base_candles": base_candles,
        "quote_candles": quote_candles,
    })

    # Create the figure
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
            y=base_candles.close
        ),
        row=1, col=1
    )

    # Add quote market candlesticks
    fig.add_trace(
        go.Scatter(
            x=quote_candles.index,
            y=quote_candles.close
        ),
        row=2, col=1
    )

    # Add horizontal lines for the base market
    fig.add_hline(
        y=controller_config["grid_config_base"]["start_price"],
        row=1, col=1,
        line=dict(color="green", width=4)  # Double sized
    )
    fig.add_hline(
        y=controller_config["grid_config_base"]["end_price"],
        row=1, col=1,
        line=dict(color="green", width=4)  # Double sized
    )
    fig.add_hline(
        y=controller_config["grid_config_base"]["limit_price"],
        row=1, col=1,
        line=dict(color="green", dash="dash")  # Dashed
    )

    # Add horizontal lines for the quote market
    fig.add_hline(
        y=controller_config["grid_config_quote"]["start_price"],
        row=2, col=1,
        line=dict(color="red", width=4)  # Double sized
    )
    fig.add_hline(
        y=controller_config["grid_config_quote"]["end_price"],
        row=2, col=1,
        line=dict(color="red", width=4)  # Double sized
    )
    fig.add_hline(
        y=controller_config["grid_config_quote"]["limit_price"],
        row=2, col=1,
        line=dict(color="red", dash="dash")  # Dashed
    )

    # Update layout
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,  # This controls the rangeslider visibility for x-axis
        xaxis2_rangeslider_visible=False,  # Disable for the second subplot
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
        paper_bgcolor='rgba(0, 0, 0, 0.1)',  # Lighter shade for the paper
        font={"color": 'white', "size": 12},  # Consistent font color and size
        height=1000,
        hovermode="x unified",
        showlegend=False
    )

    # Show the figure
    st.write(
        f"Coint Value: {extra_info['coint_value']:.3f} || "
        f"Rate Difference (Base - Quote):  {extra_info['rate_difference']:.5f}% || "
        f"Base Beta {extra_info['grid_base']['beta']:.3f} ||"
        f"Quote Beta: {extra_info['grid_quote']['beta']:.3f} || "
        f"Base Rate: {extra_info['base_rate']} ||"
        f"Quote Rate: {extra_info['quote_rate']}")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_amount_quote = st.number_input("Total Amout Quote", 1000.0)
        leverage = st.number_input("Leverage", 50)
    with col2:
        min_spread_between_orders = st.number_input("Min Spread Between Orders %", 0.02)
        stop_loss = st.number_input("Stop Loss", 0.1)
    with col3:
        take_profit = st.number_input("Take Profit", 0.0008)
        time_limit = st.number_input("Time Limit", 259200)
    with col4:
        activation_price = st.number_input("Activation Price", value=0.03)
        trailing_delta = st.number_input("Trailing Delta", value=0.005)
    controller_config["total_amount_quote"] = total_amount_quote
    controller_config["leverage"] = leverage
    controller_config["'min_spread_between_orders'"] = min_spread_between_orders / 100
    controller_config["triple_barrier_config"] = {
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'time_limit': time_limit,
        'trailing_stop': {'activation_price': activation_price, 'trailing_delta': trailing_delta}
    }


if __name__ == "__main__":
    asyncio.run(main())
