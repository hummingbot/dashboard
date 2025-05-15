import streamlit as st

from frontend.st_utils import get_backend_api_client


def render_save_config(config_base_default: str, config_data: dict):
    st.write("### Upload Config to BackendAPI")
    backend_api_client = get_backend_api_client()
    all_configs = backend_api_client.get_all_controllers_config()
    config_bases = set(config_name["id"].split("_")[0] for config_name in all_configs)
    config_base = config_base_default.split("_")[0]
    if config_base in config_bases:
        config_tag = max(float(config["id"].split("_")[-1]) for config in all_configs if config_base in config["id"])
        version, tag = str(config_tag).split(".")
        config_tag = f"{version}.{int(tag) + 1}"
    else:
        config_tag = "0.1"
    c1, c2, c3 = st.columns([1, 1, 0.5])
    with c1:
        config_base = st.text_input("Config Base", value=config_base)
    with c2:
        config_tag = st.text_input("Config Tag", value=config_tag)
    with c3:
        upload_config_to_backend = st.button("Upload")
    if upload_config_to_backend:
        config_data["id"] = f"{config_base}_{config_tag}"
        backend_api_client.add_controller_config(config_data)
        st.session_state.pop("default_config")
        st.success("Config uploaded successfully!")
