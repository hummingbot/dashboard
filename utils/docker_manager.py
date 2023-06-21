import subprocess
from typing import Dict
import yaml

import constants
from utils import os_utils


class DockerManager:
    def __init__(self):
        pass

    @staticmethod
    def get_active_containers():
        cmd = "docker ps --format '{{.Names}}'"
        output = subprocess.check_output(cmd, shell=True)
        backtestings = [container for container in output.decode().split()]
        return backtestings

    @staticmethod
    def get_exited_containers():
        cmd = "docker ps --filter status=exited --format '{{.Names}}'"
        output = subprocess.check_output(cmd, shell=True)
        containers = output.decode().split()
        return containers

    @staticmethod
    def clean_exited_containers():
        cmd = "docker container prune --force"
        subprocess.Popen(cmd, shell=True)

    def stop_active_containers(self):
        containers = self.get_active_containers()
        for container in containers:
            cmd = f"docker stop {container}"
            subprocess.Popen(cmd, shell=True)

    def stop_container(self, container_name):
        cmd = f"docker stop {container_name}"
        subprocess.Popen(cmd, shell=True)

    def start_container(self, container_name):
        cmd = f"docker start {container_name}"
        subprocess.Popen(cmd, shell=True)

    def remove_container(self, container_name):
        cmd = f"docker rm {container_name}"
        subprocess.Popen(cmd, shell=True)

    def create_download_candles_container(self, candles_config: Dict):
        os_utils.dump_dict_to_yaml(candles_config, constants.DOWNLOAD_CANDLES_CONFIG_YML)
        command = ["docker", "compose", "-p", "data_downloader", "-f",
                   "hummingbot_files/compose_files/data-downloader-compose.yml", "up", "-d"]
        subprocess.Popen(command)

    def create_broker(self):
        command = ["docker", "compose", "-p", "hummingbot-broker", "-f",
                   "hummingbot_files/compose_files/broker-compose.yml", "up", "-d", "--remove-orphans"]
        subprocess.Popen(command)

    def create_hummingbot_instance(self, instance_name):
        bot_name = f"hummingbot-{instance_name}"
        base_conf_folder = f"{constants.BOTS_FOLDER}/data_downloader/conf"
        bot_folder = f"{constants.BOTS_FOLDER}/{bot_name}"
        if not os_utils.directory_exists(bot_folder):
            create_folder_command = ["mkdir", "-p", bot_folder]
            create_folder_task = subprocess.Popen(create_folder_command)
            create_folder_task.wait()
            command = ["cp", "-rf", base_conf_folder, bot_folder]
            copy_folder_task = subprocess.Popen(command)
            copy_folder_task.wait()
        conf_file_path = f"{bot_folder}/conf/conf_client.yml"
        config = os_utils.read_yaml_file(conf_file_path)
        config['instance_id'] = bot_name
        os_utils.dump_dict_to_yaml(config, conf_file_path)
        # TODO: Mount script folder for custom scripts
        create_container_command = ["docker", "run", "-it", "-d", "--log-opt", "max-size=10m", "--log-opt",
                                    "max-file=5",
                                    "--name", bot_name,
                                    "--network", "host",
                                    "-v", f"./{bot_folder}/conf:/home/hummingbot/conf",
                                    "-v", f"./{bot_folder}/conf/connectors:/home/hummingbot/conf/connectors",
                                    "-v", f"./{bot_folder}/conf/strategies:/home/hummingbot/conf/strategies",
                                    "-v", f"./{bot_folder}/logs:/home/hummingbot/logs",
                                    "-v", "./data/:/home/hummingbot/data",
                                    # "-v", f"./{bot_folder}/scripts:/home/hummingbot/scripts",
                                    "-v", f"./{bot_folder}/certs:/home/hummingbot/certs",
                                    "-e", "CONFIG_PASSWORD=a",
                                    "dardonacci/hummingbot:development"]

        subprocess.Popen(create_container_command)
