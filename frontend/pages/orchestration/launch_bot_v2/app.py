import time
import re

import pandas as pd
import streamlit as st

from frontend.st_utils import initialize_st_page, get_backend_api_client

initialize_st_page(title="🚀 Deploy Trading Bot", icon="🙌")

# Initialize backend client
backend_api_client = get_backend_api_client()


def get_controller_configs():
    """Get all controller configurations using the new API."""
    try:
        return backend_api_client.controllers.list_controller_configs()
    except Exception as e:
        st.error(f"Failed to fetch controller configs: {e}")
        return []


def filter_hummingbot_images(images):
    """Filter images to only show Hummingbot-related ones."""
    hummingbot_images = []
    pattern = r'.+/hummingbot:'
    
    for image in images:
        try:
            if re.match(pattern, image):
                hummingbot_images.append(image)
        except Exception:
            continue
    
    return hummingbot_images


def launch_new_bot(bot_name, image_name, credentials, selected_controllers, max_global_drawdown, max_controller_drawdown):
    """Launch a new bot with the selected configuration."""
    if not bot_name:
        st.warning("You need to define the bot name.")
        return False
    if not image_name:
        st.warning("You need to select the hummingbot image.")
        return False
    if not selected_controllers:
        st.warning("You need to select the controllers configs. Please select at least one controller "
                   "config by clicking on the checkbox.")
        return False
    
    start_time_str = time.strftime("%Y%m%d-%H%M")
    full_bot_name = f"{bot_name}-{start_time_str}"
    
    try:
        # Use the new deploy_v2_controllers method
        deploy_config = {
            "instance_name": full_bot_name,
            "credentials_profile": credentials,
            "controllers_config": [config.replace(".yml", "") for config in selected_controllers],
            "image": image_name,
        }
        
        # Add optional drawdown parameters if set
        if max_global_drawdown is not None and max_global_drawdown > 0:
            deploy_config["max_global_drawdown_quote"] = max_global_drawdown
        if max_controller_drawdown is not None and max_controller_drawdown > 0:
            deploy_config["max_controller_drawdown_quote"] = max_controller_drawdown
        
        backend_api_client.bot_orchestration.deploy_v2_controllers(**deploy_config)
        st.success(f"Successfully deployed bot: {full_bot_name}")
        time.sleep(3)
        return True
        
    except Exception as e:
        st.error(f"Failed to deploy bot: {e}")
        return False


def delete_selected_configs(selected_controllers):
    """Delete selected controller configurations."""
    if selected_controllers:
        try:
            for config in selected_controllers:
                # Remove .yml extension if present
                config_name = config.replace(".yml", "")
                response = backend_api_client.controllers.delete_controller_config(config_name)
                st.success(f"Deleted {config_name}")
            return True
            
        except Exception as e:
            st.error(f"Failed to delete configs: {e}")
            return False
    else:
        st.warning("You need to select the controllers configs that you want to delete.")
        return False


# Page Header
st.markdown("Configure and deploy your automated trading strategy")

# Bot Configuration Section
st.markdown("#### 🤖 Bot Configuration")

# Create three columns for the configuration inputs
col1, col2, col3 = st.columns(3)

with col1:
    bot_name = st.text_input(
        "Instance Name",
        placeholder="Enter a unique name for your bot instance",
        key="bot_name_input"
    )

with col2:
    try:
        available_credentials = backend_api_client.accounts.list_accounts()
        credentials = st.selectbox(
            "Credentials Profile",
            options=available_credentials,
            index=0,
            key="credentials_select"
        )
    except Exception as e:
        st.error(f"Failed to fetch credentials: {e}")
        credentials = st.text_input(
            "Credentials Profile",
            value="master_account",
            key="credentials_input"
        )

with col3:
    try:
        all_images = backend_api_client.docker.get_available_images("hummingbot")
        available_images = filter_hummingbot_images(all_images)
        
        if not available_images:
            # Fallback to default if no hummingbot images found
            available_images = ["hummingbot/hummingbot:latest"]
        
        # Ensure default image is in the list
        default_image = "hummingbot/hummingbot:latest"
        if default_image not in available_images:
            available_images.insert(0, default_image)
        
        image_name = st.selectbox(
            "Hummingbot Image",
            options=available_images,
            index=0,
            key="image_select"
        )
    except Exception as e:
        st.error(f"Failed to fetch available images: {e}")
        image_name = st.text_input(
            "Hummingbot Image",
            value="hummingbot/hummingbot:latest",
            key="image_input"
        )

# Risk Management Section
st.divider()
st.markdown("#### ⚠️ Risk Management")
st.markdown("Set maximum drawdown limits in USDT to protect your capital")

col1, col2 = st.columns(2)

with col1:
    max_global_drawdown = st.number_input(
        "Max Global Drawdown (USDT)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        format="%.2f",
        help="Maximum allowed drawdown across all controllers",
        key="global_drawdown_input"
    )

with col2:
    max_controller_drawdown = st.number_input(
        "Max Controller Drawdown (USDT)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        format="%.2f",
        help="Maximum allowed drawdown per controller",
        key="controller_drawdown_input"
    )

# Controllers Section
st.divider()
st.markdown("#### 🎛️ Controller Selection")
st.markdown("Select the trading controllers you want to deploy with this bot instance")

# Get controller configs
all_controllers_config = get_controller_configs()

# Prepare data for the table
data = []
for config in all_controllers_config:
    # Handle case where config might be a string instead of dict
    if isinstance(config, str):
        st.warning(f"Unexpected config format: {config}. Expected a dictionary.")
        continue
    
    # Handle both old and new config format
    config_name = config.get("config_name", config.get("id", "Unknown"))
    config_data = config.get("config", config)  # New format has config nested
    
    connector_name = config_data.get("connector_name", "Unknown")
    trading_pair = config_data.get("trading_pair", "Unknown")
    total_amount_quote = float(config_data.get("total_amount_quote", 0))
    
    # Extract controller info
    controller_name = config_data.get("controller_name", config_name)
    controller_type = config_data.get("controller_type", "generic")
    
    # Fix config base and version splitting
    config_parts = config_name.split("_")
    if len(config_parts) > 1:
        version = config_parts[-1]
        config_base = "_".join(config_parts[:-1])
    else:
        config_base = config_name
        version = "NaN"
    
    data.append({
        "Select": False,  # Checkbox column
        "Config Base": config_base,
        "Version": version,
        "Controller Name": controller_name,
        "Controller Type": controller_type,
        "Connector": connector_name,
        "Trading Pair": trading_pair,
        "Amount (USDT)": f"${total_amount_quote:,.2f}",
        "_config_name": config_name  # Hidden column for reference
    })

# Display info and action buttons
if data:
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Use data_editor with checkbox column for selection
    edited_df = st.data_editor(
        df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select controllers to deploy or delete",
                default=False,
            ),
            "_config_name": None,  # Hide this column
        },
        disabled=[col for col in df.columns if col != "Select"],  # Only allow editing the Select column
        hide_index=True,
        use_container_width=True,
        key="controller_table"
    )
    
    # Get selected controllers from the edited dataframe
    selected_controllers = [
        row["_config_name"] 
        for _, row in edited_df.iterrows() 
        if row["Select"]
    ]

    # Display action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
            if selected_controllers:
                if delete_selected_configs(selected_controllers):
                    st.rerun()
            else:
                st.warning("Please select at least one controller to delete")
    
    with col2:
        if st.button("🚀 Deploy Bot", type="primary", use_container_width=True):
            if selected_controllers:
                with st.spinner('Starting Bot... This process may take a few seconds'):
                    if launch_new_bot(bot_name, image_name, credentials, selected_controllers, 
                                    max_global_drawdown, max_controller_drawdown):
                        st.rerun()
            else:
                st.warning("Please select at least one controller to deploy")

else:
    st.warning("No controller configurations available. Please create some configurations first.")