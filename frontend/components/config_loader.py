import streamlit as st
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT

from backend.services.backend_api_client import BackendAPIClient
from frontend.utils import generate_random_name

backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


def get_default_config_loader(controller_name: str):
    all_configs = backend_api_client.get_all_controllers_config()
    existing_configs = [config["id"].split("-")[0] for config in all_configs]
    default_dict = {"id": generate_random_name(existing_configs)}
    with st.expander("Configurations", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            use_default_config = st.checkbox("Use default config", value=True)
        if use_default_config:
            st.session_state["default_config"] = default_dict
        else:
            with c2:
                configs = [config for config in all_configs if config["controller_name"] == controller_name]
                default_config = st.selectbox("Select a config", [config["id"] for config in configs])
                st.session_state["default_config"] = next((config for config in all_configs if config["id"] == default_config), None)
                if st.session_state["default_config"] is None:
                    st.session_state["default_config"] = default_dict
                else:
                    st.session_state["default_config"]["id"] = st.session_state["default_config"]["id"].split("_")[0]
