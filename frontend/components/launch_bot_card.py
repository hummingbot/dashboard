import os
import time

from docker_manager import DockerManager
import streamlit as st
from streamlit_elements import mui, lazy

import constants
from utils.os_utils import get_directories_from_directory
from .dashboard import Dashboard


class LaunchBotCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_master_bot_running = False
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
        self._base_bot_config = "master_bot_conf"

    def _set_bot_name(self, event):
        self._bot_name = event.target.value

    def _set_image_name(self, event):
        self._image_name = event.target.value

    def _set_base_bot_config(self, event):
        self._base_bot_config = event.target.value

    def launch_new_bot(self):
        if self._bot_name and self._image_name:
            bot_name = f"hummingbot-{self._bot_name}"
            DockerManager().create_hummingbot_instance(instance_name=bot_name,
                                                       base_conf_folder=f"{constants.HUMMINGBOT_TEMPLATES}/{self._base_bot_config}/.",
                                                       target_conf_folder=f"{constants.BOTS_FOLDER}/{bot_name}/.",
                                                       controllers_folder=constants.CONTROLLERS_PATH,
                                                       controllers_config_folder=constants.CONTROLLERS_CONFIG_PATH,
                                                       image=self._image_name)
            with st.spinner('Starting Master Configs instance... This process may take a few seconds'):
                time.sleep(3)
        else:
            st.warning("You need to define the bot name and image in order to create one.")

    def __call__(self):
        active_containers = DockerManager.get_active_containers()
        self.is_master_bot_running = "hummingbot-master_bot_conf" in active_containers
        password_file_path = os.path.join(constants.HUMMINGBOT_TEMPLATES + "/master_bot_conf/conf",
                                          '.password_verification')
        is_master_password_set = os.path.isfile(password_file_path)
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.Typography("🚀 Create Instance", variant="h5")

            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                with mui.Grid(item=True, xs=8):
                    if not is_master_password_set:
                            base_warning = "You need to set a master password in order to use the dashboard."
                            if self.is_master_bot_running:
                                mui.Alert(f"{base_warning} The Master Configs instance is running."
                                            f" Attach to it in Terminal to set the master password.", severity="success")
                            else:
                                mui.Alert(f"{base_warning} Master Configs instance isn't running. Start it and"
                                            f" set the master password to continue.", severity="error")
                    else:
                        mui.Alert("The new instance will contain the credentials configured in the following base instance:",
                                severity="info")
                with mui.Grid(item=True, xs=4):
                    master_configs = [conf.split("/")[-2] for conf in
                                    get_directories_from_directory(constants.HUMMINGBOT_TEMPLATES) if
                                    "bot_conf" in conf]
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Base Configs")
                        with mui.Select(label="Base Configs", defaultValue=master_configs[0],
                                        variant="standard", onChange=lazy(self._set_base_bot_config)):
                            for master_config in master_configs:
                                mui.MenuItem(master_config, value=master_config)
                with mui.Grid(item=True, xs=4):
                    mui.TextField(label="Instance Name", variant="outlined", onChange=lazy(self._set_bot_name),
                                    sx={"width": "100%"})
                with mui.Grid(item=True, xs=4):
                    mui.TextField(label="Hummingbot Image", 
                                  defaultValue="hummingbot/hummingbot:latest",
                                  variant="outlined",
                                  placeholder="hummingbot-[name]",
                                  onChange=lazy(self._set_image_name),
                                  sx={"width": "100%"})

                with mui.Grid(item=True, xs=4):
                    with mui.Button(onClick=self.launch_new_bot,
                                    variant="outlined",
                                    color="success",
                                    sx={"width": "100%", "height": "100%"}):
                        mui.icon.AddCircleOutline()
                        mui.Typography("Create")

