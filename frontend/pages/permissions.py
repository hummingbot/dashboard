from st_pages import Page, Section


def main_page():
    return [Page("main.py", "Hummingbot Dashboard", "📊")]


def public_pages():
    return [
        Section("Config Generator", "🎛️"),
        Page("frontend/pages/config/grid_strike/app.py", "Grid Strike", "🎳"),
        Page("frontend/pages/config/pmm_simple/app.py", "PMM Simple", "👨‍🏫"),
        Page("frontend/pages/config/pmm_dynamic/app.py", "PMM Dynamic", "👩‍🏫"),
        Page("frontend/pages/config/dman_maker_v2/app.py", "D-Man Maker V2", "🤖"),
        Page("frontend/pages/config/bollinger_v1/app.py", "Bollinger V1", "📈"),
        Page("frontend/pages/config/macd_bb_v1/app.py", "MACD_BB V1", "📊"),
        Page("frontend/pages/config/supertrend_v1/app.py", "SuperTrend V1", "👨‍🔬"),
        Page("frontend/pages/config/xemm_controller/app.py", "XEMM Controller", "⚡️"),
        Section("Data", "💾"),
        Page("frontend/pages/data/download_candles/app.py", "Download Candles", "💹"),
        Section("Community Pages", "👨‍👩‍👧‍👦"),
        Page("frontend/pages/data/token_spreads/app.py", "Token Spreads", "🧙"),
        Page("frontend/pages/data/tvl_vs_mcap/app.py", "TVL vs Market Cap", "🦉"),
    ]


def private_pages():
    return [
        Section("Bot Orchestration", "🐙"),
        Page("frontend/pages/orchestration/instances/app.py", "Instances", "🦅"),
        Page("frontend/pages/orchestration/launch_bot_v2/app.py", "Deploy V2", "🚀"),
        Page("frontend/pages/orchestration/credentials/app.py", "Credentials", "🔑"),
        Page("frontend/pages/orchestration/portfolio/app.py", "Portfolio", "💰"),
    ]
