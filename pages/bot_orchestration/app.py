import time
from types import SimpleNamespace

import constants
import pandas as pd
import streamlit as st
from streamlit_elements import elements, mui, html, lazy, sync

from docker_manager import DockerManager
from hbotrc import BotCommands

from ui_components.bot_performance_card import BotPerformanceCard
from ui_components.card import Card
from ui_components.dashboard import Dashboard
from utils.st_utils import initialize_st_page

initialize_st_page(title="Bot Orchestration", icon="🐙")

if "is_broker_running" not in st.session_state:
    st.session_state.is_broker_running = ""

if "active_bots" not in st.session_state:
    st.session_state.active_bots = {}

def update_containers_info(docker_manager):
    active_containers = docker_manager.get_active_containers()
    st.session_state.is_broker_running = "hummingbot-broker" in active_containers

    # TODO: Improve performance by only updating the changed containers since now a new instance of the broker is created
    active_bots = {container: {
        "bot_name": container,
        "broker_client": BotCommands(host='localhost', port=1883, username='admin', password='password',
                                     bot_id=container)
    } for container in active_containers if
        "hummingbot-" in container and "broker" not in container}
    for container in active_bots.keys():
        # TODO: Implement start date
        broker_client = active_bots[container]["broker_client"]
        status = broker_client.status()
        history = broker_client.history()
        is_running = "No strategy is currently running" not in status.msg
        active_bots[container]["is_running"] = is_running
        active_bots[container]["status"] = status.msg
        active_bots[container]["trades"] = history.trades
    st.session_state.active_bots = active_bots


# Start content here
docker_manager = DockerManager()

update_containers_info(docker_manager)
orchestrate, create, manage = st.tabs(["Orchestrate", "Create", "Manage"])

with orchestrate:
    c1, c2 = st.columns([0.8, 0.2])
    if not st.session_state.is_broker_running:
        with c1:
            st.error("Hummingbot Broker is not running, please start it if you want to manage your bots.")
        with c2:
            if st.button("Create Hummingbot Broker"):
                docker_manager.create_broker()
    else:
        with c1:
            st.success("Hummingbot Broker is running")
        with c2:
            # TODO: Add configuration variables for broker creation
            if st.button("Stop Hummingbot Broker"):
                docker_manager.stop_container("hummingbot-broker")

        st.write("## 🦅Active Hummingbot Instances")
        quantity_of_active_bots = len(st.session_state.active_bots)
        if quantity_of_active_bots > 0:
            # TODO: Make layout configurable
            cols = 3
            rows = quantity_of_active_bots // cols + 1
            active_instances_board = Dashboard()
            for bot, config in st.session_state.active_bots.items():
                st.session_state.active_bots[bot]["bot_performance_card"] = BotPerformanceCard(active_instances_board, 0, 0, 4, 4)

            with elements("active_instances_board"):
                with active_instances_board():
                    for bot, config in st.session_state.active_bots.items():
                        st.session_state.active_bots[bot]["bot_performance_card"](config)
        st.write(st.session_state.active_bots)

        # if len(all_instances) > 0:
        #     with c1:
        #         df = pd.DataFrame(all_instances, columns=["instance_name", "status"])
        #         df["selected"] = False
        #         edited_df = st.data_editor(df[["selected", "instance_name", "status"]])
        #         selected_instances = edited_df[edited_df["selected"]]["instance_name"].tolist()
        #     with c2:
        #         stop_instances = st.button("Stop Selected Instances")
        #         start_instances = st.button("Start Selected Instances")
        #         clean_instances = st.button("Clean Selected Instances")
        #
        #         if stop_instances:
        #             for instance in selected_instances:
        #                 docker_manager.stop_container(instance)
        #
        #         if start_instances:
        #             for instance in selected_instances:
        #                 docker_manager.start_container(instance)
        #
        #         if clean_instances:
        #             for instance in selected_instances:
        #                 docker_manager.remove_container(instance)
        # else:
        #     st.info("No active hummingbot instances")
        #
        # st.write("---")
        #
        # if len(active_hummingbot_instances) > 0 and is_broker_running:
        #     broker_clients = {instance_name[0]: BotCommands(
        #         host='localhost',
        #         port=1883,
        #         username='admin',
        #         password='password',
        #         bot_id=instance_name[0],
        #     ) for instance_name in active_hummingbot_instances}
        #     instance_names = [instance_name[0] for instance_name in active_hummingbot_instances]
        #     tabs = st.tabs([instance_name for instance_name in instance_names])
        #     for i, tab in enumerate(tabs):
        #         with tab:
        #             instance_name = instance_names[i]
        #             client = broker_clients[instance_name]
        #             status = client.status()
        #             bot_stopped = "No strategy is currently running" in status.msg
        #             strategy = None
        #             c1, c2 = st.columns([0.8, 0.2])
        #             with c1:
        #                 if bot_stopped:
        #                     strategy = st.text_input(
        #                         "Strategy config or Script to run (strategy will be the name of the config file"
        #                         "and script script_name.py)",
        #                         key=f"strategy-{instance_name}")
        #                     st.info("The bot is currently stopped. Start a strategy to get the bot status")
        #             with c2:
        #                 if strategy:
        #                     run_strategy = st.button("Run Strategy", key=f"run-{instance_name}")
        #                     is_script = strategy.endswith(".py")
        #                     if run_strategy:
        #                         if is_script:
        #                             client.start(script=strategy)
        #                         else:
        #                             client.import_strategy(strategy=strategy.replace(".yml", ""))
        #                             time.sleep(0.5)
        #                             client.start(strategy)
        #                 status = st.button("Get Status", key=f"status-{instance_name}")
        #                 stop_strategy = st.button("Stop Strategy", key=f"stop-{instance_name}")
        #             with c1:
        #                 if status:
        #                     status = client.status()
        #                     st.write(status.msg)
        #                 if stop_strategy:
        #                     client.stop(strategy)
        #                     st.success("Strategy stopped")

with create:
    st.write("## 🚀Create Hummingbot Instance")
    c11, c12 = st.columns([0.8, 0.2])
    with c11:
        instance_name = st.text_input("Instance Name")
    with c12:
        st.write()
        create_instance = st.button("Create Instance")
        if create_instance:
            bot_name = f"hummingbot-{instance_name}"
            docker_manager.create_hummingbot_instance(instance_name=bot_name,
                                                      base_conf_folder=f"{constants.BOTS_FOLDER}/master_bot_conf/",
                                                      target_conf_folder=f"{constants.BOTS_FOLDER}/{bot_name}")

with manage:
    with elements("monaco_editors"):
        # Streamlit Elements embeds Monaco code and diff editor that powers Visual Studio Code.
        # You can configure editor's behavior and features with the 'options' parameter.
        #
        # Streamlit Elements uses an unofficial React implementation (GitHub links below for
        # documentation).

        from streamlit_elements import editor

        if "content" not in st.session_state:
            st.session_state.content = "Default value"

        mui.Typography("Content: ", st.session_state.content)


        def update_content(value):
            st.session_state.content = value


        editor.Monaco(
            height=1200,
            defaultValue=st.session_state.content,
            onChange=lazy(update_content),
            defaultLanguage="python"
        )

        mui.Button("Update content", onClick=sync())
