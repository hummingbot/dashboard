import os
import time

from docker_manager import DockerManager
import streamlit as st
from streamlit_elements import mui, sync

import constants
from .dashboard import Dashboard


class LaunchBrokerCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_broker_running = False

    def manage_broker_container(self):
        if self.is_broker_running:
            DockerManager().stop_container("hummingbot-broker")
            with st.spinner('Stopping Hummingbot Broker... you will not going to be able to manage bots anymore.'):
                time.sleep(5)
        else:
            DockerManager().create_broker()
            with st.spinner('Starting Hummingbot Broker... This process may take a few seconds'):
                time.sleep(20)

    def __call__(self):
        active_containers = DockerManager.get_active_containers()
        self.is_broker_running = "hummingbot-broker" in active_containers
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.Typography("🐙 Manage Broker", variant="h4")
            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                with mui.Grid(item=True, xs=8):
                    if self.is_broker_running:
                        mui.Alert("Hummingbot Broker is running, you can control your bots now!", severity="success")
                    else:
                        mui.Alert("Humminngbot Broker is not running, start it to start controlling your bots.",
                                  severity="error")

                with mui.Grid(item=True, xs=4):
                    button_text = "Stop" if self.is_broker_running else "Start"
                    color = "error" if self.is_broker_running else "success"
                    icon = mui.icon.Stop if self.is_broker_running else mui.icon.PlayCircle
                    with mui.Button(onClick=self.manage_broker_container,
                                    color=color,
                                    variant="outlined",
                                    sx={"width": "100%", "height": "100%"}):
                        icon()
                        mui.Typography(button_text)


