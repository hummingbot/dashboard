import streamlit as st


def main_page():
    return [st.Page("frontend/pages/landing.py", title="Hummingbot Dashboard", icon="📊", url_path="landing")]


def public_pages():
    return {
        "Config Generator": [
            st.Page("frontend/pages/config/grid_strike/app.py", title="Grid Strike", icon="🎳", url_path="grid_strike"),
            st.Page("frontend/pages/config/pmm_simple/app.py", title="PMM Simple", icon="👨‍🏫", url_path="pmm_simple"),
            st.Page("frontend/pages/config/pmm_dynamic/app.py", title="PMM Dynamic", icon="👩‍🏫", url_path="pmm_dynamic"),
            st.Page("frontend/pages/config/dman_maker_v2/app.py", title="D-Man Maker V2", icon="🤖", url_path="dman_maker_v2"),
            st.Page("frontend/pages/config/bollinger_v1/app.py", title="Bollinger V1", icon="📈", url_path="bollinger_v1"),
            st.Page("frontend/pages/config/macd_bb_v1/app.py", title="MACD_BB V1", icon="📊", url_path="macd_bb_v1"),
            st.Page("frontend/pages/config/supertrend_v1/app.py", title="SuperTrend V1", icon="👨‍🔬", url_path="supertrend_v1"),
            st.Page("frontend/pages/config/xemm_controller/app.py", title="XEMM Controller", icon="⚡️", url_path="xemm_controller"),
        ],
        "Data": [
            st.Page("frontend/pages/data/download_candles/app.py", title="Download Candles", icon="💹", url_path="download_candles"),
        ],
        "Community Pages": [
            st.Page("frontend/pages/data/tvl_vs_mcap/app.py", title="TVL vs Market Cap", icon="🦉", url_path="tvl_vs_mcap"),
        ]
    }


def private_pages():
    return {
        "Bot Orchestration": [
            st.Page("frontend/pages/orchestration/instances/app.py", title="Instances", icon="🦅", url_path="instances"),
            st.Page("frontend/pages/orchestration/launch_bot_v2/app.py", title="Deploy V2", icon="🚀", url_path="launch_bot_v2"),
            st.Page("frontend/pages/orchestration/credentials/app.py", title="Credentials", icon="🔑", url_path="credentials"),
            st.Page("frontend/pages/orchestration/portfolio/app.py", title="Portfolio", icon="💰", url_path="portfolio"),
            st.Page("frontend/pages/orchestration/trading/app.py", title="Trading", icon="🪄", url_path="trading"),
            st.Page("frontend/pages/orchestration/archived_bots/app.py", title="Archived Bots", icon="🗃️", url_path="archived_bots"),
        ]
    }
