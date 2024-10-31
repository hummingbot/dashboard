import inspect
import os.path
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from st_pages import add_page_title, show_pages
from yaml import SafeLoader

from CONFIG import AUTH_SYSTEM_ENABLED
from frontend.pages.permissions import main_page, private_pages, public_pages


def initialize_st_page(title: str, icon: str, layout="wide", initial_sidebar_state="expanded"):
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )
    caller_frame = inspect.currentframe().f_back

    add_page_title(layout=layout, initial_sidebar_state=initial_sidebar_state)

    current_directory = Path(os.path.dirname(inspect.getframeinfo(caller_frame).filename))
    readme_path = current_directory / "README.md"
    with st.expander("About This Page"):
        st.write(readme_path.read_text())


def download_csv_button(df: pd.DataFrame, filename: str, key: str):
    csv = df.to_csv(index=False).encode('utf-8')
    return st.download_button(
        label="Download CSV",
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


def get_backend_api_client():
    from backend.services.backend_api_client import BackendAPIClient
    from CONFIG import BACKEND_API_HOST, BACKEND_API_PASSWORD, BACKEND_API_PORT, BACKEND_API_USERNAME
    try:
        backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT,
                                                           username=BACKEND_API_USERNAME, password=BACKEND_API_PASSWORD)
        if not backend_api_client.is_docker_running():
            st.error("Docker is not running. Please make sure Docker is running.")
            st.stop()
        return backend_api_client
    except Exception:
        st.stop()


def auth_system():
    if not AUTH_SYSTEM_ENABLED:
        show_pages(main_page() + private_pages() + public_pages())
    else:
        with open('credentials.yml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        if "authenticator" not in st.session_state or "authentication_status" not in st.session_state or not st.session_state.get(
                "authentication_status", False):
            st.session_state.authenticator = stauth.Authenticate(
                config['credentials'],
                config['cookie']['name'],
                config['cookie']['key'],
                config['cookie']['expiry_days'],
            )
            show_pages(main_page() + public_pages())
            st.session_state.authenticator.login()
            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')
            elif st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')
        else:
            st.session_state.authenticator.logout(location="sidebar")
            st.sidebar.write(f'Welcome *{st.session_state["name"]}*')
            show_pages(main_page() + private_pages() + public_pages())
