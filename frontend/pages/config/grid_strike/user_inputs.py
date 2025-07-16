import streamlit as st
from hummingbot.core.data_type.common import OrderType, PositionMode, TradeType

from frontend.pages.config.utils import get_candles


def get_price_range_defaults(connector_name: str, trading_pair: str, interval: str, days: int = 7):
    """Fetch candles and compute default price range based on recent min/max prices."""
    try:
        candles = get_candles(
            connector_name=connector_name,
            trading_pair=trading_pair,
            interval=interval,
            days=days
        )
        current_price = float(candles['close'].iloc[-1])
        min_price = float(candles['low'].quantile(0.05))
        max_price = float(candles['high'].quantile(0.95))
        return round(min_price, 2), round(current_price, 2), round(max_price, 2)
    except Exception as e:
        st.warning(f"Could not fetch price data: {str(e)}. Using default values.")
        return 40000.0, 42000.0, 44000.0  # Fallback defaults


def user_inputs():
    # Split the page into two columns for the expanders
    left_col, right_col = st.columns(2)
    with left_col:
        # Combined Basic, Amount, and Grid Configuration
        with st.expander("Grid Configuration", expanded=True):
            # Basic parameters
            c1, c2 = st.columns(2)
            with c1:
                connector_name = st.text_input("Connector Name", value="binance_perpetual")
                # Side selection
                side = st.selectbox(
                    "Side",
                    options=["BUY", "SELL"],
                    index=0,
                    help="Trading direction for the grid"
                )
                leverage = st.number_input("Leverage", min_value=1, value=20)
            with c2:
                trading_pair = st.text_input("Trading Pair", value="WLD-USDT")
                # Amount parameter
                total_amount_quote = st.number_input(
                    "Total Amount (Quote)",
                    min_value=0.0,
                    value=200.0,
                    help="Total amount in quote currency to use for trading"
                )
                position_mode = st.selectbox(
                    "Position Mode",
                    options=["HEDGE", "ONEWAY"],
                    index=0
                )
            # Grid price parameters
            with c1:
                # Get default price ranges based on current market data
                min_price, current_price, max_price = get_price_range_defaults(
                    connector_name,
                    trading_pair,
                    "1h",  # Default interval for price range calculation
                    30     # Default days for price range calculation
                )
                if side == "BUY":
                    start_price = min(min_price, current_price)
                    end_price = max(current_price, max_price)
                    limit_price = start_price * 0.95
                else:
                    start_price = max(max_price, current_price)
                    end_price = min(current_price, min_price)
                    limit_price = start_price * 1.05
                # Price configuration with meaningful defaults
                start_price = st.number_input(
                    "Start Price",
                    value=start_price,
                    format="%.2f",
                    help="Grid start price"
                )
                
                end_price = st.number_input(
                    "End Price",
                    value=end_price,
                    format="%.2f",
                    help="Grid end price"
                )
                
                limit_price = st.number_input(
                    "Limit Price",
                    value=limit_price,
                    format="%.2f",
                    help="Price limit to stop the strategy"
                )
            
            with c2:
                # Grid spacing configuration
                min_spread = st.number_input(
                    "Min Spread Between Orders",
                    min_value=0.0000,
                    value=0.0001,
                    format="%.4f",
                    help="Minimum price difference between orders",
                    step=0.0001
                )
                
                min_order_amount = st.number_input(
                    "Min Order Amount (Quote)",
                    min_value=1.0,
                    value=6.0,
                    help="Minimum amount for each order in quote currency"
                )
                
                max_open_orders = st.number_input(
                    "Maximum Open Orders",
                    min_value=1,
                    value=3,
                    help="Maximum number of active orders in the grid"
                )
        
    with right_col:
        # Order configuration
        with st.expander("Order Configuration", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                max_orders_per_batch = st.number_input(
                    "Max Orders Per Batch",
                    min_value=1,
                    value=1,
                    help="Maximum number of orders to place at once"
                )
            with c2:
                order_frequency = st.number_input(
                    "Order Frequency (s)",
                    min_value=1,
                    value=2,
                    help="Time between order placements in seconds"
                )
            with c3:
                activation_bounds = st.number_input(
                    "Activation Bounds",
                    min_value=0.0,
                    value=0.01,
                    format="%.4f",
                    help="Price deviation to trigger updates"
                )
        
        # Triple barrier configuration 
        with st.expander("Triple Barrier Configuration", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                # Order types
                open_order_type_options = ["LIMIT", "LIMIT_MAKER", "MARKET"]
                open_order_type = st.selectbox(
                    "Open Order Type",
                    options=open_order_type_options,
                    index=1,  # Default to MARKET
                    key="open_order_type"
                )
                
                take_profit_order_type_options = ["LIMIT", "LIMIT_MAKER", "MARKET"]
                take_profit_order_type = st.selectbox(
                    "Take Profit Order Type",
                    options=take_profit_order_type_options,
                    index=1,  # Default to MARKET
                    key="tp_order_type"
                )

            with c2:
                # Barrier values
                take_profit = st.number_input(
                    "Take Profit",
                    min_value=0.0,
                    value=0.0001,
                    format="%.4f",
                    help="Price movement percentage for take profit"
                )
                
                stop_loss = st.number_input(
                    "Stop Loss",
                    min_value=0.0,
                    value=0.1,
                    format="%.4f",
                    help="Price movement percentage for stop loss (0 for none)"
                )
                
                # Keep position parameter
                keep_position = st.checkbox(
                    "Keep Position",
                    value=False,
                    help="Keep the position open after grid execution"
                )
        # Chart configuration
        with st.expander("Chart Configuration", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                candles_connector = st.text_input(
                    "Candles Connector",
                    value=connector_name,  # Use same connector as trading by default
                    help="Connector to fetch price data from"
                )
            with c2:
                interval = st.selectbox(
                    "Interval",
                    options=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
                    index=4,  # Default to 1h
                    help="Candlestick interval"
                )
            with c3:
                days_to_visualize = st.number_input(
                    "Days to Display",
                    min_value=1,
                    max_value=365,
                    value=30,
                    help="Number of days of historical data to display"
                )


    
    # Convert stop_loss to None if it's zero
    stop_loss_value = stop_loss if stop_loss > 0 else None
    
    # Prepare triple barrier config
    triple_barrier_config = {
        "open_order_type": OrderType[open_order_type],
        "stop_loss": stop_loss_value,
        "take_profit": take_profit,
        "take_profit_order_type": OrderType[take_profit_order_type],
        "time_limit": None,
    }

    return {
        "controller_name": "grid_strike",
        "controller_type": "generic",
        "connector_name": connector_name,
        "candles_connector": candles_connector,
        "trading_pair": trading_pair,
        "interval": interval,
        "days_to_visualize": days_to_visualize,
        "leverage": leverage,
        "side": TradeType[side],
        "start_price": start_price,
        "end_price": end_price,
        "limit_price": limit_price,
        "position_mode": PositionMode[position_mode],
        "total_amount_quote": total_amount_quote,
        "min_spread_between_orders": min_spread,
        "min_order_amount_quote": min_order_amount,
        "max_open_orders": max_open_orders,
        "max_orders_per_batch": max_orders_per_batch,
        "order_frequency": order_frequency,
        "activation_bounds": activation_bounds,
        "triple_barrier_config": triple_barrier_config,
        "keep_position": keep_position,
        "candles_config": []
    } 