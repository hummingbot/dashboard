import streamlit as st


def render_backtesting_metrics(summary_results, title: str = "Backtesting Metrics"):
    net_pnl = summary_results.get('net_pnl', 0)
    net_pnl_quote = summary_results.get('net_pnl_quote', 0)
    total_volume = summary_results.get('total_volume', 0)
    total_executors_with_position = summary_results.get('total_executors_with_position', 0)

    max_drawdown_usd = summary_results.get('max_drawdown_usd', 0)
    max_drawdown_pct = summary_results.get('max_drawdown_pct', 0)
    sharpe_ratio = summary_results.get('sharpe_ratio', 0)
    profit_factor = summary_results.get('profit_factor', 0)

    # Displaying KPIs in Streamlit
    st.write(f"### {title}")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric(label="Net PNL (Quote)", value=f"{net_pnl_quote:.2f}", delta=f"{net_pnl:.2%}")
    col2.metric(label="Max Drawdown (USD)", value=f"{max_drawdown_usd:.2f}", delta=f"{max_drawdown_pct:.2%}")
    col3.metric(label="Total Volume (Quote)", value=f"{total_volume:.2f}")
    col4.metric(label="Sharpe Ratio", value=f"{sharpe_ratio:.2f}")
    col5.metric(label="Profit Factor", value=f"{profit_factor:.2f}")
    col6.metric(label="Total Executors with Position", value=total_executors_with_position)


def render_accuracy_metrics(summary_results, mode="v"):
    accuracy = summary_results.get('accuracy', 0)
    total_long = summary_results.get('total_long', 0)
    total_short = summary_results.get('total_short', 0)
    accuracy_long = summary_results.get('accuracy_long', 0)
    accuracy_short = summary_results.get('accuracy_short', 0)

    st.write("#### Accuracy Metrics")
    if mode == "v":
        st.metric(label="Global Accuracy", value=f"{accuracy:.2%}")
        st.metric(label="Total Long", value=total_long)
        st.metric(label="Total Short", value=total_short)
        st.metric(label="Accuracy Long", value=f"{accuracy_long:.2%}")
        st.metric(label="Accuracy Short", value=f"{accuracy_short:.2%}")
    elif mode == "h":
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="Global Accuracy", value=f"{accuracy:.2%}")
        with col2:
            st.metric(label="Total Long", value=total_long)
        with col3:
            st.metric(label="Total Short", value=total_short)
        with col4:
            st.metric(label="Accuracy Long", value=f"{accuracy_long:.2%}")
        with col5:
            st.metric(label="Accuracy Short", value=f"{accuracy_short:.2%}")
    elif mode == "t":
        st.write(f"""
        - Global Accuracy: {accuracy:.2%}
        - Total Long: {total_long}
        - Total Short: {total_short}
        - Accuracy Long: {accuracy_long:.2%}
        - Accuracy Short: {accuracy_short:.2%}
        """)
    else:
        raise ValueError("Invalid mode. Possible values are 'v', 'h' and 't'.")


def render_close_types(summary_results, mode="v"):
    st.write("#### Close Types")
    close_types = summary_results.get('close_types', {})
    if mode == "v":
        st.metric(label="TAKE PROFIT", value=f"{close_types.get('TAKE_PROFIT', 0)}")
        st.metric(label="STOP LOSS", value=f"{close_types.get('STOP_LOSS', 0)}")
        st.metric(label="TIME LIMIT", value=f"{close_types.get('TIME_LIMIT', 0)}")
        st.metric(label="EARLY STOP", value=f"{close_types.get('EARLY_STOP', 0)}")
    elif mode == "h":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="TAKE PROFIT", value=f"{close_types.get('TAKE_PROFIT', 0)}")
        with col2:
            st.metric(label="STOP LOSS", value=f"{close_types.get('STOP_LOSS', 0)}")
        with col3:
            st.metric(label="TIME LIMIT", value=f"{close_types.get('TIME_LIMIT', 0)}")
        with col4:
            st.metric(label="EARLY STOP", value=f"{close_types.get('EARLY_STOP', 0)}")
    elif mode == "t":
        st.write(f"""
        - Take Profit: {close_types.get('TAKE_PROFIT', 0)}
        - Stop Loss: {close_types.get('STOP_LOSS', 0)}
        - Time Limit: {close_types.get('TIME_LIMIT', 0)}
        - Early Stop: {close_types.get('EARLY_STOP', 0)}
        """)
    else:
        raise ValueError("Invalid mode. Possible values are 'v', 'h' and 't'.")
