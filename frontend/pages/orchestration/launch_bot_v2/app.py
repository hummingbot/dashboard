import re
import time

import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

initialize_st_page(icon="🙌", show_readme=False)

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


# Page Header with dark futuristic styling
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1419 0%, #1a1d23 50%, #2d3748 100%);
    padding: 40px;
    border-radius: 20px;
    margin-bottom: 30px;
    text-align: center;
    color: #e2e8f0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    border: 1px solid rgba(100, 255, 218, 0.1);
    position: relative;
    overflow: hidden;
">
<div style="
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #64ffda 0%, #00bcd4 50%, #64ffda 100%);
"></div>
<h1 style="
    margin: 0; 
    font-size: 3rem; 
    font-weight: 800;
    background: linear-gradient(135deg, #64ffda 0%, #00bcd4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(100, 255, 218, 0.5);
">🚀 Deploy Trading Bot</h1>
<p style="
    margin: 15px 0 0 0; 
    font-size: 1.3rem; 
    opacity: 0.8;
    color: #94a3b8;
    font-weight: 300;
">Configure and deploy your automated trading strategy</p>
</div>
""", unsafe_allow_html=True)

# Bot Configuration Section
with st.container(border=True):
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f1419 0%, #1a1d23 100%);
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid rgba(100, 255, 218, 0.15);
        position: relative;
    ">
    <div style="
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #64ffda 0%, #00bcd4 100%);
        border-radius: 2px;
    "></div>
    <div style="display: flex; align-items: baseline; gap: 12px;">
        <h3 style="
            margin: 0; 
            color: #64ffda;
            font-weight: 600;
            font-size: 1.3rem;
        ">🤖 Bot Configuration:</h3>
        <span style="
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 400;
        ">Set up your bot instance with basic configuration</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

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
with st.container(border=True):
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a0f0f 0%, #211414 100%);
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 107, 107, 0.2);
        position: relative;
    ">
    <div style="
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #ff6b6b 0%, #ee5a24 100%);
        border-radius: 2px;
    "></div>
    <div style="display: flex; align-items: baseline; gap: 12px;">
        <h3 style="
            margin: 0; 
            color: #ff6b6b;
            font-weight: 600;
            font-size: 1.3rem;
        ">⚠️ Risk Management:</h3>
        <span style="
            color: #94a3b8;
            font-size: 0.9rem;
            font-weight: 400;
        ">Set maximum drawdown limits in USDT to protect your capital</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

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
with st.container(border=True):
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f1a0f 0%, #141f14 100%);
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid rgba(76, 175, 80, 0.2);
        position: relative;
    ">
    <div style="
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #4caf50 0%, #2e7d32 100%);
        border-radius: 2px;
    "></div>
    <div style="display: flex; align-items: baseline; gap: 12px;">
        <h3 style="
            margin: 0; 
            color: #4caf50;
            font-weight: 600;
            font-size: 1.3rem;
        ">🎛️ Controller Selection:</h3>
        <span style="
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 400;
        ">Select the trading controllers you want to deploy with this bot instance</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

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

        # Display selected count with futuristic styling
        if selected_controllers:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #0a2f20 0%, #0f3f2a 100%);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                border: 1px solid rgba(76, 175, 80, 0.3);
                text-align: center;
            ">
            <span style="
                color: #4caf50;
                font-weight: 600;
                font-size: 1.1rem;
            ">✅ {len(selected_controllers)} controller(s) selected for deployment</span>
            </div>
            """, unsafe_allow_html=True)

        # Display action buttons with enhanced styling
        st.markdown("""
        <div style="
            margin-top: 30px;
            padding: 20px 0;
            border-top: 1px solid rgba(100, 255, 218, 0.1);
        "></div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                if selected_controllers:
                    if delete_selected_configs(selected_controllers):
                        st.rerun()
                else:
                    st.warning("Please select at least one controller to delete")
        
        with col2:
            deploy_button_style = "primary" if selected_controllers else "secondary"
            if st.button("🚀 Deploy Bot", type=deploy_button_style, use_container_width=True):
                if selected_controllers:
                    with st.spinner('🚀 Starting Bot... This process may take a few seconds'):
                        if launch_new_bot(bot_name, image_name, credentials, selected_controllers, 
                                        max_global_drawdown, max_controller_drawdown):
                            st.rerun()
                else:
                    st.warning("Please select at least one controller to deploy")

    else:
        st.warning("⚠️ No controller configurations available. Please create some configurations first.")