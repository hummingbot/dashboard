import inspect
import os.path
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from streamlit.commands.page_config import InitialSideBarState, Layout
from yaml import SafeLoader

from CONFIG import AUTH_SYSTEM_ENABLED
from frontend.pages.permissions import main_page, private_pages, public_pages


def initialize_st_page(title: Optional[str] = None, icon: str = "🤖", layout: Layout = 'wide',
                       initial_sidebar_state: InitialSideBarState = "expanded",
                       show_readme: bool = True):
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )
    
    # Add page title
    if title:
        st.title(title)
    
    # Get caller frame info safely
    frame: Optional[Union[inspect.FrameInfo, inspect.Traceback]] = None
    try:
        caller_frame = inspect.currentframe()
        if caller_frame is not None:
            caller_frame = caller_frame.f_back
            if caller_frame is not None:
                frame = inspect.getframeinfo(caller_frame)
    except Exception:
        pass

    if frame is not None and show_readme:
        current_directory = Path(os.path.dirname(frame.filename))
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
    from hummingbot_api_client import SyncHummingbotAPIClient
    import atexit

    from CONFIG import BACKEND_API_HOST, BACKEND_API_PASSWORD, BACKEND_API_PORT, BACKEND_API_USERNAME

    # Use Streamlit session state to store singleton instance
    if 'backend_api_client' not in st.session_state or st.session_state.backend_api_client is None:
        try:
            # Create and enter the client context
            # Ensure URL has proper protocol
            if not BACKEND_API_HOST.startswith(('http://', 'https://')):
                base_url = f"http://{BACKEND_API_HOST}:{BACKEND_API_PORT}"
            else:
                base_url = f"{BACKEND_API_HOST}:{BACKEND_API_PORT}"
            
            client = SyncHummingbotAPIClient(
                base_url=base_url,
                username=BACKEND_API_USERNAME,
                password=BACKEND_API_PASSWORD
            )
            # Initialize the client using context manager
            client.__enter__()
            
            # Register cleanup function to properly exit the context manager
            def cleanup_client():
                try:
                    if 'backend_api_client' in st.session_state and st.session_state.backend_api_client is not None:
                        st.session_state.backend_api_client.__exit__(None, None, None)
                        st.session_state.backend_api_client = None
                except Exception:
                    pass  # Ignore cleanup errors
            
            # Register cleanup with atexit and session state
            atexit.register(cleanup_client)
            if 'cleanup_registered' not in st.session_state:
                st.session_state.cleanup_registered = True
                # Also register cleanup for session state changes
                st.session_state.backend_api_client_cleanup = cleanup_client
            
            # Check Docker after initialization
            if not client.docker.is_running():
                st.error("Docker is not running. Please make sure Docker is running.")
                cleanup_client()  # Clean up before stopping
                st.stop()
                
            st.session_state.backend_api_client = client
        except Exception as e:
            st.error(f"Failed to initialize API client: {str(e)}")
            st.stop()
    
    return st.session_state.backend_api_client


def auth_system():
    if not AUTH_SYSTEM_ENABLED:
        return {
            "Main": main_page(),
            **private_pages(),
            **public_pages(),
        }
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
            # Show only public pages for non-authenticated users
            st.session_state.authenticator.login()
            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')
            elif st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')
            return {
                "Main": main_page(),
                **public_pages()
            }
        else:
            st.session_state.authenticator.logout(location="sidebar")
            st.sidebar.write(f'Welcome *{st.session_state["name"]}*')
            # Show all pages for authenticated users
            return {
                "Main": main_page(),
                **private_pages(),
                **public_pages(),
            }
