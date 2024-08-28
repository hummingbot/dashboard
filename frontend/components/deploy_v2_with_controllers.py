import time

import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client


class LaunchV2WithControllers:
    DEFAULT_COLUMNS = [
        "id", "controller_name", "controller_type", "connector_name",
        "trading_pair", "total_amount_quote", "max_loss_quote", "stop_loss",
        "take_profit", "trailing_stop", "time_limit", "selected"
    ]

    def __init__(self):
        self._backend_api_client = get_backend_api_client()
        self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
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

    def launch_new_bot(self):
        if self._bot_name and self._image_name and self._controller_config_selected:
            start_time_str = time.strftime("%Y.%m.%d_%H.%M")
            bot_name = f"{self._bot_name}-{start_time_str}"
            script_config = {
                "name": bot_name,
                "content": {
                    "markets": {},
                    "candles_config": [],
                    "controllers_config": self._controller_config_selected,
                    "config_update_interval": 20,
                    "script_file_name": "v2_with_controllers.py",
                    "time_to_cash_out": None,
                }
            }

            self._backend_api_client.add_script_config(script_config)
            deploy_config = {
                "instance_name": bot_name,
                "script": "v2_with_controllers.py",
                "script_config": bot_name + ".yml",
                "image": self._image_name,
                "credentials_profile": self._credentials,
            }
            self._backend_api_client.create_hummingbot_instance(deploy_config)
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
            connector_name = config.get("connector_name", "Unknown")
            trading_pair = config.get("trading_pair", "Unknown")
            total_amount_quote = config.get("total_amount_quote", 0)
            stop_loss = config.get("stop_loss", 0)
            take_profit = config.get("take_profit", 0)
            trailing_stop = config.get("trailing_stop", {"activation_price": 0, "trailing_delta": 0})
            time_limit = config.get("time_limit", 0)
            data.append({
                "selected": False,
                "id": config["id"],
                "controller_name": config["controller_name"],
                "controller_type": config["controller_type"],
                "connector_name": connector_name,
                "trading_pair": trading_pair,
                "total_amount_quote": total_amount_quote,
                "max_loss_quote": total_amount_quote * stop_loss / 2,
                "stop_loss": f"{stop_loss:.2%}",
                "take_profit": f"{take_profit:.2%}",
                "trailing_stop": f"{trailing_stop['activation_price']:.2%} / {trailing_stop['trailing_delta']:.2%}",
                "time_limit": time_limit,
            })

        df = pd.DataFrame(data)

        edited_df = st.data_editor(df, hide_index=True)

        self._controller_config_selected = [f"{config}.yml" for config in
                                            edited_df[edited_df["selected"]]["id"].tolist()]
        st.write(self._controller_config_selected)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 0.3])
        with c1:
            self._bot_name = st.text_input("Instance Name")
        with c2:
            available_images = self._backend_api_client.get_available_images("hummingbot")
            self._image_name = st.selectbox("Hummingbot Image", available_images,
                                            index=available_images.index("hummingbot/hummingbot:latest"))
        with c3:
            available_credentials = self._backend_api_client.get_accounts()
            self._credentials = st.selectbox("Credentials", available_credentials, index=0)
        with c4:
            deploy_button = st.button("Deploy Bot")
        if deploy_button:
            self.launch_new_bot()
