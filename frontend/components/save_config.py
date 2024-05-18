import streamlit as st

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient


def render_save_config(controller_name: str, config_data: dict):
    st.write("### Upload Config to BackendAPI")
    c1, c2, c3 = st.columns([1, 1, 0.5])
    connector = config_data.get("connector_name", "")
    trading_pair = config_data.get("trading_pair", "")
    with c1:
        config_base = st.text_input("Config Base", value=f"{controller_name}-{connector}-{trading_pair.split('-')[0]}")
    with c2:
        config_tag = st.text_input("Config Tag", value="1.1")
    with c3:
        upload_config_to_backend = st.button("Upload")
    if upload_config_to_backend:
        config_data["id"] = f"{config_base}-{config_tag}"
        backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)
        backend_api_client.add_controller_config(config_data)
        st.success("Config uploaded successfully!")
