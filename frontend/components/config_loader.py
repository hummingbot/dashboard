import streamlit as st

from frontend.st_utils import get_backend_api_client
from frontend.utils import generate_random_name

backend_api_client = get_backend_api_client()


def get_default_config_loader(controller_name: str):
    try:
        all_configs = backend_api_client.controllers.list_controller_configs()
    except Exception as e:
        st.error(f"Failed to fetch controller configs: {e}")
        all_configs = []
    
    # Handle both old and new config format
    existing_configs = []
    for config in all_configs:
        config_name = config.get("config_name", config.get("id", ""))
        if config_name:
            existing_configs.append(config_name.split("_")[0])
    
    default_dict = {"id": generate_random_name(existing_configs)}
    default_config = st.session_state.get("default_config", default_dict)
    config_controller_name = default_config.get("controller_name")
    if default_config is None or controller_name != config_controller_name:
        st.session_state["default_config"] = default_dict
    with st.expander("Configurations", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            use_default_config = st.checkbox("Use default config", value=True)
        with c2:
            if not use_default_config:
                # Filter configs by controller name
                configs = []
                for config in all_configs:
                    config_data = config.get("config", config)
                    if config_data.get("controller_name") == controller_name:
                        configs.append(config)
                
                if len(configs) > 0:
                    config_names = [config.get("config_name", config.get("id", "Unknown")) for config in configs]
                    selected_config_name = st.selectbox("Select a config", config_names)
                    
                    # Find the selected config
                    selected_config = None
                    for config in configs:
                        if config.get("config_name", config.get("id", "")) == selected_config_name:
                            selected_config = config
                            break
                    
                    if selected_config:
                        # Use the config data, handling both old and new formats
                        config_data = selected_config.get("config", selected_config)
                        st.session_state["default_config"] = config_data.copy()
                        st.session_state["default_config"]["id"] = selected_config_name.split("_")[0]
                else:
                    st.warning("No existing configs found for this controller.")
