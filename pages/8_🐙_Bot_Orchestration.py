import pandas as pd

from hbotrc import BotCommands

import streamlit as st

from utils.docker_manager import DockerManager

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🐙 Bot Orchestration")
st.write("---")

docker_manager = DockerManager()

active_containers = docker_manager.get_active_containers()
exited_containers = docker_manager.get_exited_containers()



st.write("## 🚀Create Hummingbot Instance")
c11, c12 = st.columns([0.8, 0.2])
with c11:
    instance_name = st.text_input("Instance Name")
with c12:
    st.write()
    create_instance = st.button("Create Instance")
    if create_instance:
        docker_manager.create_hummingbot_instance(instance_name)

st.write("---")

st.write("## 🦅Hummingbot Instances")

st.write("This section will let you control your hummingbot instances.")

c1, c2 = st.columns([0.8, 0.2])
active_hummingbot_instances = [(container, "active") for container in active_containers if "hummingbot-" in container
                               and "broker" not in container]
exited_hummingbot_instances = [(container, "exited") for container in exited_containers if "hummingbot-" in container
                               and "broker" not in container]
all_instances = active_hummingbot_instances + exited_hummingbot_instances
if len(all_instances) > 0:
    with c1:
        df = pd.DataFrame(all_instances, columns=["instance_name", "status"])
        df["selected"] = False
        edited_df = st.data_editor(df[["selected", "instance_name", "status"]])
        selected_instances = edited_df[edited_df["selected"]]["instance_name"].tolist()
    with c2:
        stop_instances = st.button("Stop Selected Instances")
        start_instances = st.button("Start Selected Instances")
        clean_instances = st.button("Clean Selected Instances")

        if stop_instances:
            for instance in selected_instances:
                docker_manager.stop_container(instance)

        if start_instances:
            for instance in selected_instances:
                docker_manager.start_container(instance)

        if clean_instances:
            for instance in selected_instances:
                docker_manager.remove_container(instance)
else:
    st.info("No active hummingbot instances")

st.write("---")
st.write("## 📩Hummingbot Broker")
if "hummingbot-broker" not in active_containers:
    c1, c2 = st.columns([0.9, 0.1])
    with c1:
        st.error("Hummingbot Broker is not running")
    with c2:
        # TODO: Add configuration variables for broker creation
        create_broker = st.button("Create Hummingbot Broker")
        if create_broker:
            docker_manager.create_broker()
else:
    c1, c2 = st.columns([0.9, 0.1])
    with c1:
        st.success("Hummingbot Broker is running")
    with c2:
        # TODO: Make that the hummingbot client checks if the broker is running if the config is on like gateway
        stop_broker = st.button("Stop Hummingbot Broker")
        if stop_broker:
            docker_manager.stop_container("hummingbot-broker")
    if len(active_hummingbot_instances) > 0:
        broker_clients = {instance_name[0]: BotCommands(
                                    host='localhost',
                                    port=1883,
                                    username='admin',
                                    password='38828943.Dardonacci',
                                    bot_id=instance_name[0],
                                ) for instance_name in active_hummingbot_instances}
        instance_names = [instance_name[0] for instance_name in active_hummingbot_instances]
        tabs = st.tabs([instance_name for instance_name in instance_names])
        for i, tab in enumerate(tabs):
            with tab:
                instance_name = instance_names[i]
                client = broker_clients[instance_name]
                status = client.status()
                bot_stopped = "No strategy is currently running" in status.msg
                strategy = None
                c1, c2 = st.columns([0.8, 0.2])
                with c1:
                    if bot_stopped:
                        strategy = st.text_input("Strategy config or Script to run (strategy will be .yml and script .py)",
                                                 key=f"strategy-{instance_name}")
                        st.info("The bot is currently stopped. Start a strategy to get the bot status")
                with c2:
                    if strategy:
                        run_strategy = st.button("Run Strategy", key=f"run-{instance_name}")
                        is_script = strategy.endswith(".py")
                        if run_strategy:
                            if is_script:
                                client.start(script=strategy)
                            else:
                                client.import_strategy(strategy=strategy)
                                client.stop(strategy)
                    status = st.button("Get Status", key=f"status-{instance_name}")
                    stop_strategy = st.button("Stop Strategy", key=f"stop-{instance_name}")
                with c1:
                    if status:
                        status = client.status()
                        st.write(status.msg)
                    if stop_strategy:
                        client.stop(strategy)
                        st.success("Strategy stopped")
