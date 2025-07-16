import streamlit as st
import nest_asyncio

from frontend.st_utils import get_backend_api_client

nest_asyncio.apply()

def render_save_config(config_base_default: str, config_data: dict):
    st.write("### Upload Config to BackendAPI")
    backend_api_client = get_backend_api_client()
    try:
        all_configs = backend_api_client.controllers.list_controller_configs()
    except Exception as e:
        st.error(f"Failed to fetch controller configs: {e}")
        return
    
    # Check if we're editing an existing config
    existing_config_id = config_data.get("id", "")
    is_existing_config = bool(existing_config_id and any(config.get("id") == existing_config_id for config in all_configs))
    
    if is_existing_config:
        # For existing configs, preserve the original ID
        config_base = existing_config_id.split("_")[0] if "_" in existing_config_id else existing_config_id
        config_tag = existing_config_id.split("_")[-1] if "_" in existing_config_id else "0.1"
    else:
        # For new configs, generate a new version
        config_bases = set()
        for config in all_configs:
            config_name = config.get("id")
            if config_name:
                config_bases.add(config_name.split("_")[0])
        config_base = config_base_default.split("_")[0]
        if config_base in config_bases:
            config_tags = []
            for config in all_configs:
                config_name = config.get("id")
                if config_name and config_base in config_name:
                    try:
                        config_tags.append(float(config_name.split("_")[-1]))
                    except (ValueError, IndexError):
                        continue
            if config_tags:
                config_tag = max(config_tags)
                version, tag = str(config_tag).split(".")
                config_tag = f"{version}.{int(tag) + 1}"
            else:
                config_tag = "0.1"
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
        config_name = f"{config_base}_{config_tag}"
        config_data["id"] = config_name
        try:
            backend_api_client.controllers.create_or_update_controller_config(
                config_name=config_name,
                config=config_data
            )
            st.session_state.pop("default_config", None)
            st.success("Config uploaded successfully!")
        except Exception as e:
            st.error(f"Failed to upload config: {e}")
