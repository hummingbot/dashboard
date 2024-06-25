import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from frontend.components.config_loader import get_default_config_loader
from frontend.components.executors_distribution import get_executors_distribution_inputs
from frontend.components.save_config import render_save_config

# Import submodules
from frontend.components.backtesting import backtesting_section
from frontend.pages.config.pmm_dynamic.spread_and_price_multipliers import get_pmm_dynamic_multipliers
from frontend.pages.config.pmm_dynamic.user_inputs import user_inputs
from frontend.pages.config.utils import get_candles
from frontend.st_utils import initialize_st_page, get_backend_api_client
from frontend.visualization import theme
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.executors_distribution import create_executors_distribution_traces
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_close_types, \
    render_accuracy_metrics
from frontend.visualization.indicators import get_macd_traces
from frontend.visualization.utils import add_traces_to_fig

# Initialize the Streamlit page
initialize_st_page(title="PMM Dynamic", icon="👩‍🏫")
backend_api_client = get_backend_api_client()

# Page content
st.text("This tool will let you create a config for PMM Dynamic, backtest and upload it to the Backend API.")
get_default_config_loader("pmm_dynamic")
# Get user inputs
inputs = user_inputs()
st.write("### Visualizing MACD and NATR indicators for PMM Dynamic")
st.text("The MACD is used to shift the mid price and the NATR to make the spreads dynamic. "
        "In the order distributions graph, we are going to see the values of the orders affected by the average NATR")
days_to_visualize = st.number_input("Days to Visualize", min_value=1, max_value=365, value=30)
# Load candle data
candles = get_candles(connector_name=inputs["candles_connector"], trading_pair=inputs["candles_trading_pair"], interval=inputs["interval"], days=days_to_visualize)
with st.expander("Visualizing PMM Dynamic Indicators", expanded=True):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, subplot_titles=('Candlestick with Bollinger Bands', 'MACD', "Price Multiplier", "Spreads Multiplier"),
                        row_heights=[0.8, 0.2, 0.2, 0.2])
    add_traces_to_fig(fig, [get_candlestick_trace(candles)], row=1, col=1)
    add_traces_to_fig(fig, get_macd_traces(df=candles, macd_fast=inputs["macd_fast"], macd_slow=inputs["macd_slow"], macd_signal=inputs["macd_signal"]), row=2, col=1)
    price_multiplier, spreads_multiplier = get_pmm_dynamic_multipliers(candles, inputs["macd_fast"], inputs["macd_slow"], inputs["macd_signal"], inputs["natr_length"])
    add_traces_to_fig(fig, [go.Scatter(x=candles.index, y=price_multiplier, name="Price Multiplier", line=dict(color="blue"))], row=3, col=1)
    add_traces_to_fig(fig, [go.Scatter(x=candles.index, y=spreads_multiplier, name="Base Spread", line=dict(color="red"))], row=4, col=1)
    fig.update_layout(**theme.get_default_layout(height=1000))
    fig.update_yaxes(tickformat=".2%", row=3, col=1)
    fig.update_yaxes(tickformat=".2%", row=4, col=1)
    st.plotly_chart(fig, use_container_width=True)

st.write("### Executors Distribution")
st.write("The order distributions are affected by the average NATR. This means that if the first order has a spread of "
         "1 and the NATR is 0.005, the first order will have a spread of 0.5% of the mid price.")
buy_spread_distributions, sell_spread_distributions, buy_order_amounts_pct, sell_order_amounts_pct = get_executors_distribution_inputs(use_custom_spread_units=True)
inputs["buy_spreads"] = [spread * 100 for spread in buy_spread_distributions]
inputs["sell_spreads"] = [spread * 100 for spread in sell_spread_distributions]
inputs["buy_amounts_pct"] = buy_order_amounts_pct
inputs["sell_amounts_pct"] = sell_order_amounts_pct
st.session_state["default_config"].update(inputs)
with st.expander("Executor Distribution:", expanded=True):
    natr_avarage = spreads_multiplier.mean()
    buy_spreads = [spread * natr_avarage for spread in inputs["buy_spreads"]]
    sell_spreads = [spread * natr_avarage for spread in inputs["sell_spreads"]]
    st.write(f"Average NATR: {natr_avarage:.2%}")
    fig = create_executors_distribution_traces(buy_spreads, sell_spreads, inputs["buy_amounts_pct"], inputs["sell_amounts_pct"], inputs["total_amount_quote"])
    st.plotly_chart(fig, use_container_width=True)

bt_results = backtesting_section(inputs, backend_api_client)
if bt_results:
    fig = create_backtesting_figure(
        df=bt_results["processed_data"],
        executors=bt_results["executors"],
        config=inputs)
    c1, c2 = st.columns([0.9, 0.1])
    with c1:
        render_backtesting_metrics(bt_results["results"])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        render_accuracy_metrics(bt_results["results"])
        st.write("---")
        render_close_types(bt_results["results"])
st.write("---")
render_save_config(st.session_state["default_config"]["id"], st.session_state["default_config"])
