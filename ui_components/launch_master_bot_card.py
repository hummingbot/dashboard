import os
import time

from docker_manager import DockerManager
import streamlit as st
from streamlit_elements import mui

import constants
from .dashboard import Dashboard


class LaunchMasterBotCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_master_bot_running = False

    def manage_master_bot_container(self):
        if self.is_master_bot_running:
            DockerManager().stop_container("hummingbot-master_bot_conf")
            with st.spinner('Stopping Master Bot Conf... you will not going to be able to add more credentials.'):
                time.sleep(5)
        else:
            DockerManager().create_hummingbot_instance(instance_name="hummingbot-master_bot_conf",
                                                       base_conf_folder="hummingbot_files/templates/master_bot_conf/.",
                                                       target_conf_folder="hummingbot_files/templates/master_bot_conf/."
                                                       )
            with st.spinner('Starting Master Bot Conf... This process may take a few seconds'):
                time.sleep(3)

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
                mui.icon.OndemandVideo()
                mui.Typography("🔑 Master Bot Config")
            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                with mui.Grid(item=True, xs=8):
                    if not is_master_password_set:
                        base_warning = "You need to set a master password in order to use the dashboard."
                        if self.is_master_bot_running:
                            mui.Alert(f"{base_warning} Master Bot Conf is running, run in a terminal docker attach "
                                      f"hummingbot-master_bot_conf and set the master password.", severity="success")
                        else:
                            mui.Alert(f"{base_warning} Master Bot Conf is not running, press start, attach the instance"
                                      f" in your terminal and introduce the password to continue.", severity="error")
                    else:
                        if self.is_master_bot_running:
                            mui.Alert("Master Bot Conf is running, you can add more credentials. Run in a terminal "
                                      "docker attach hummingbot-master_bot_conf", severity="success")
                        else:
                            mui.Alert("Master Bot Conf is not running, press start to add more credentials.",
                                      severity="error")

                with mui.Grid(item=True, xs=4):
                    button_text = "Stop" if self.is_master_bot_running else "Start"
                    color = "error" if self.is_master_bot_running else "success"
                    icon = mui.icon.Stop if self.is_master_bot_running else mui.icon.PlayCircle
                    with mui.Button(onClick=self.manage_master_bot_container,
                                    color=color,
                                    variant="outlined",
                                    sx={"width": "100%", "height": "100%"}):
                        icon()
                        mui.Typography(button_text)


