import streamlit as st
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT

from backend.services.backend_api_client import BackendAPIClient

backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


def get_default_config_loader(controller_name: str):
    use_default_config = st.checkbox("Use default config", value=True)
    all_configs = backend_api_client.get_all_controllers_config()
    if use_default_config:
        st.session_state["default_config"] = {}
    else:
        configs = [config for config in all_configs if config["controller_name"] == controller_name]
        default_config = st.selectbox("Select a config", [config["id"] for config in configs])
        st.session_state["default_config"] = next((config for config in all_configs if config["id"] == default_config), {})
