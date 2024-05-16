def get_default_layout(title, height=800, width=1800):
    return {
        "template": "plotly_dark",
        "title": title,
        "plot_bgcolor": 'rgba(0, 0, 0, 0)',  # Transparent background
        "paper_bgcolor": 'rgba(0, 0, 0, 0.1)',  # Lighter shade for the paper
        "font": {"color": 'white', "size": 12},  # Consistent font color and size
        "height": height,
        "width": width,
        "margin": {"l": 20, "r": 20, "t": 50, "b": 20}
    }


def get_color_scheme():
    return {
        'upper_band': '#4682B4',
        'middle_band': '#FFD700',
        'lower_band': '#32CD32',
        'buy_signal': '#1E90FF',
        'sell_signal': '#FF0000',
        'buy': '#32CD32',  # Green for buy orders
        'sell': '#FF6347',  # Tomato red for sell orders
        'candlestick_increasing': '#2ECC71',
        'candlestick_decreasing': '#E74C3C',
        'macd_line': '#FFA500',  # Orange
        'macd_signal': '#800080',  # Purple
        'macd_histogram_positive': '#32CD32',  # Green
        'macd_histogram_negative': '#FF6347',  # Red
        'spread': '#00BFFF',  # Deep Sky Blue
        'break_even': '#FFD700',  # Gold
        'take_profit': '#32CD32',  # Green
        'order_amount': '#1E90FF',  # Dodger Blue
        'cum_amount': '#4682B4',  # Steel Blue
        'stop_loss': '#FF0000',  # Red
        'cum_unrealized_pnl': '#FFA07A'  # Light Salmon

    }


