import time
import re

import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client


class LaunchV2WithControllers:
    DEFAULT_COLUMNS = [
        "id", "controller_name", "controller_type", "connector_name",
        "trading_pair", "total_amount_quote", "selected"
    ]

    def __init__(self):
        self._backend_api_client = get_backend_api_client()
        self._controller_configs_available = self._get_controller_configs()
        self._controller_config_selected = []
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
        self._credentials = "master_account"

    def _set_bot_name(self, bot_name):
        self._bot_name = bot_name

    def _set_image_name(self, image_name):
        self._image_name = image_name

    def _set_credentials(self, credentials):
        self._credentials = credentials
    
    def _get_controller_configs(self):
        """Get all controller configurations using the new API."""
        try:
            return self._backend_api_client.controllers.list_controller_configs()
        except Exception as e:
            st.error(f"Failed to fetch controller configs: {e}")
            return []
    
    @staticmethod
    def _filter_hummingbot_images(images):
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

    def launch_new_bot(self):
        if self._bot_name and self._image_name and self._controller_config_selected:
            start_time_str = time.strftime("%Y.%m.%d_%H.%M")
            bot_name = f"{self._bot_name}-{start_time_str}"
            
            try:
                # Use the new deploy_v2_controllers method
                deploy_config = {
                    "instance_name": bot_name,
                    "credentials_profile": self._credentials,
                    "controllers_config": [config.replace(".yml", "") for config in self._controller_config_selected],
                    "image": self._image_name,
                }
                
                self._backend_api_client.bot_orchestration.deploy_v2_controllers(**deploy_config)
            except Exception as e:
                st.error(f"Failed to deploy bot: {e}")
                return
            with st.spinner('Starting Bot... This process may take a few seconds'):
                time.sleep(3)
        else:
            st.warning("You need to define the bot name and select the controllers configs "
                       "that you want to deploy.")

    def __call__(self):
        st.write("#### Select the controllers configs that you want to deploy.")
        all_controllers_config = self._controller_configs_available
        data = []
        for config in all_controllers_config:
            # Handle both old and new config format
            config_name = config.get("config_name", config.get("id", "Unknown"))
            config_data = config.get("config", config)  # New format has config nested
            
            connector_name = config_data.get("connector_name", "Unknown")
            trading_pair = config_data.get("trading_pair", "Unknown")
            total_amount_quote = config_data.get("total_amount_quote", 0)
            stop_loss = config_data.get("stop_loss", 0)
            take_profit = config_data.get("take_profit", 0)
            trailing_stop = config_data.get("trailing_stop", {"activation_price": 0, "trailing_delta": 0})
            time_limit = config_data.get("time_limit", 0)
            
            # Extract controller info from config
            controller_name = config_data.get("controller_name", config_name)
            controller_type = config_data.get("controller_type", "Unknown")
            
            data.append({
                "selected": False,
                "id": config_name,
                "controller_name": controller_name,
                "controller_type": controller_type,
                "connector_name": connector_name,
                "trading_pair": trading_pair,
                "total_amount_quote": total_amount_quote,
            })

        df = pd.DataFrame(data)

        edited_df = st.data_editor(df, hide_index=True)

        selected_configs = edited_df[edited_df["selected"]]["id"].tolist()
        self._controller_config_selected = [f"{config}.yml" for config in selected_configs]
        st.write(self._controller_config_selected)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 0.3])
        with c1:
            self._bot_name = st.text_input("Instance Name")
        with c2:
            try:
                all_images = self._backend_api_client.docker.get_available_images("hummingbot")
                available_images = self._filter_hummingbot_images(all_images)
                
                if not available_images:
                    # Fallback to default if no hummingbot images found
                    available_images = ["hummingbot/hummingbot:latest"]
                
                # Ensure default image is in the list
                default_image = "hummingbot/hummingbot:latest"
                if default_image not in available_images:
                    available_images.insert(0, default_image)
                
                default_index = 0
                if default_image in available_images:
                    default_index = available_images.index(default_image)
                
                self._image_name = st.selectbox("Hummingbot Image", available_images, index=default_index)
            except Exception as e:
                st.error(f"Failed to fetch available images: {e}")
                self._image_name = st.text_input("Hummingbot Image", value="hummingbot/hummingbot:latest")
        with c3:
            try:
                available_credentials = self._backend_api_client.accounts.list_accounts()
                self._credentials = st.selectbox("Credentials", available_credentials, index=0)
            except Exception as e:
                st.error(f"Failed to fetch accounts: {e}")
                self._credentials = st.text_input("Credentials", value="master_account")
        with c4:
            deploy_button = st.button("Deploy Bot")
        if deploy_button:
            self.launch_new_bot()
