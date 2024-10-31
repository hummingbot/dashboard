from typing import Dict, Optional

import pandas as pd
import requests
import streamlit as st
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo
from requests.auth import HTTPBasicAuth


class BackendAPIClient:
    """
    This class is a client to interact with the backend API. The Backend API is a REST API that provides endpoints to
    create new Hummingbot instances, start and stop them, add new script and controller config files, and get the status
    of the active bots.
    """
    _shared_instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "BackendAPIClient":
        if cls._shared_instance is None:
            cls._shared_instance = BackendAPIClient(*args, **kwargs)
        return cls._shared_instance

    def __init__(self, host: str = "localhost", port: int = 8000, username: str = "admin", password: str = "admin"):
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.auth = HTTPBasicAuth(username, password)

    def post(self, endpoint: str, payload: Optional[Dict] = None, params: Optional[Dict] = None):
        """
        Post request to the backend API.
        :param params:
        :param endpoint:
        :param payload:
        :return:
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=payload, params=params, auth=self.auth)
        return self._process_response(response)

    def get(self, endpoint: str):
        """
        Get request to the backend API.
        :param endpoint:
        :return:
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, auth=self.auth)
        return self._process_response(response)

    @staticmethod
    def _process_response(response):
        if response.status_code == 401:
            st.error("You are not authorized to access Backend API. Please check your credentials.")
            return
        elif response.status_code == 400:
            st.error(response.json()["detail"])
            return
        return response.json()

    def is_docker_running(self):
        """Check if Docker is running."""
        endpoint = "is-docker-running"
        return self.get(endpoint)["is_docker_running"]

    def pull_image(self, image_name: str):
        """Pull a Docker image."""
        endpoint = "pull-image"
        return self.post(endpoint, payload={"image_name": image_name})

    def list_available_images(self, image_name: str):
        """List available images by name."""
        endpoint = f"available-images/{image_name}"
        return self.get(endpoint)

    def list_active_containers(self):
        """List all active containers."""
        endpoint = "active-containers"
        return self.get(endpoint)

    def list_exited_containers(self):
        """List all exited containers."""
        endpoint = "exited-containers"
        return self.get(endpoint)

    def clean_exited_containers(self):
        """Clean up exited containers."""
        endpoint = "clean-exited-containers"
        return self.post(endpoint, payload=None)

    def remove_container(self, container_name: str, archive_locally: bool = True, s3_bucket: str = None):
        """Remove a specific container."""
        endpoint = f"remove-container/{container_name}"
        params = {"archive_locally": archive_locally}
        if s3_bucket:
            params["s3_bucket"] = s3_bucket
        return self.post(endpoint, params=params)

    def stop_container(self, container_name: str):
        """Stop a specific container."""
        endpoint = f"stop-container/{container_name}"
        return self.post(endpoint)

    def start_container(self, container_name: str):
        """Start a specific container."""
        endpoint = f"start-container/{container_name}"
        return self.post(endpoint)

    def create_hummingbot_instance(self, instance_config: dict):
        """Create a new Hummingbot instance."""
        endpoint = "create-hummingbot-instance"
        return self.post(endpoint, payload=instance_config)

    def start_bot(self, start_bot_config: dict):
        """Start a Hummingbot bot."""
        endpoint = "start-bot"
        return self.post(endpoint, payload=start_bot_config)

    def stop_bot(self, bot_name: str, skip_order_cancellation: bool = False, async_backend: bool = True):
        """Stop a Hummingbot bot."""
        endpoint = "stop-bot"
        return self.post(endpoint, payload={"bot_name": bot_name, "skip_order_cancellation": skip_order_cancellation,
                                            "async_backend": async_backend})

    def import_strategy(self, strategy_config: dict):
        """Import a trading strategy to a bot."""
        endpoint = "import-strategy"
        return self.post(endpoint, payload=strategy_config)

    def get_bot_status(self, bot_name: str):
        """Get the status of a bot."""
        endpoint = f"get-bot-status/{bot_name}"
        return self.get(endpoint)

    def get_bot_history(self, bot_name: str):
        """Get the historical data of a bot."""
        endpoint = f"get-bot-history/{bot_name}"
        return self.get(endpoint)

    def get_active_bots_status(self):
        """
        Retrieve the cached status of all active bots.
        Returns a JSON response with the status and data of active bots.
        """
        endpoint = "get-active-bots-status"
        return self.get(endpoint)

    def get_all_controllers_config(self):
        """Get all controller configurations."""
        endpoint = "all-controller-configs"
        return self.get(endpoint)

    def get_available_images(self, image_name: str = "hummingbot"):
        """Get available images."""
        endpoint = f"available-images/{image_name}"
        return self.get(endpoint)["available_images"]

    def add_script_config(self, script_config: dict):
        """Add a new script configuration."""
        endpoint = "add-script-config"
        return self.post(endpoint, payload=script_config)

    def add_controller_config(self, controller_config: dict):
        """Add a new controller configuration."""
        endpoint = "add-controller-config"
        config = {
            "name": controller_config["id"],
            "content": controller_config
        }
        return self.post(endpoint, payload=config)

    def delete_controller_config(self, controller_name: str):
        """Delete a controller configuration."""
        url = "delete-controller-config"
        return self.post(url, params={"config_name": controller_name})

    def get_real_time_candles(self, connector: str, trading_pair: str, interval: str, max_records: int):
        """Get candles data."""
        endpoint = "real-time-candles"
        payload = {
            "connector": connector,
            "trading_pair": trading_pair,
            "interval": interval,
            "max_records": max_records
        }
        return self.post(endpoint, payload=payload)

    def get_historical_candles(self, connector: str, trading_pair: str, interval: str, start_time: int, end_time: int):
        """Get historical candles data."""
        endpoint = "historical-candles"
        payload = {
            "connector_name": connector,
            "trading_pair": trading_pair,
            "interval": interval,
            "start_time": start_time,
            "end_time": end_time
        }
        return self.post(endpoint, payload=payload)

    def run_backtesting(self, start_time: int, end_time: int, backtesting_resolution: str, trade_cost: float, config: dict):
        """Run backtesting."""
        endpoint = "run-backtesting"
        payload = {
            "start_time": start_time,
            "end_time": end_time,
            "backtesting_resolution": backtesting_resolution,
            "trade_cost": trade_cost,
            "config": config
        }
        backtesting_results = self.post(endpoint, payload=payload)
        if "error" in backtesting_results:
            raise Exception(backtesting_results["error"])
        if "processed_data" not in backtesting_results:
            data = None
        else:
            data = pd.DataFrame(backtesting_results["processed_data"])
        if "executors" not in backtesting_results:
            executors = []
        else:
            executors = [ExecutorInfo(**executor) for executor in backtesting_results["executors"]]
        return {
            "processed_data": data,
            "executors": executors,
            "results": backtesting_results["results"]
        }

    def get_all_configs_from_bot(self, bot_name: str):
        """Get all configurations from a bot."""
        endpoint = f"all-controller-configs/bot/{bot_name}"
        return self.get(endpoint)

    def stop_controller_from_bot(self, bot_name: str, controller_id: str):
        """Stop a controller from a bot."""
        endpoint = f"update-controller-config/bot/{bot_name}/{controller_id}"
        config = {"manual_kill_switch": True}
        return self.post(endpoint, payload=config)

    def start_controller_from_bot(self, bot_name: str, controller_id: str):
        """Start a controller from a bot."""
        endpoint = f"update-controller-config/bot/{bot_name}/{controller_id}"
        config = {"manual_kill_switch": False}
        return self.post(endpoint, payload=config)

    def get_connector_config_map(self, connector_name: str):
        """Get connector configuration map."""
        endpoint = f"connector-config-map/{connector_name}"
        return self.get(endpoint)

    def get_all_connectors_config_map(self):
        """Get all connector configuration maps."""
        endpoint = "all-connectors-config-map"
        return self.get(endpoint)

    def add_account(self, account_name: str):
        """Add a new account."""
        endpoint = "add-account"
        return self.post(endpoint, params={"account_name": account_name})

    def delete_account(self, account_name: str):
        """Delete an account."""
        endpoint = "delete-account"
        return self.post(endpoint, params={"account_name": account_name})

    def delete_credential(self, account_name: str, connector_name: str):
        """Delete credentials."""
        endpoint = f"delete-credential/{account_name}/{connector_name}"
        return self.post(endpoint)

    def add_connector_keys(self, account_name: str, connector_name: str, connector_config: dict):
        """Add connector keys."""
        endpoint = f"add-connector-keys/{account_name}/{connector_name}"
        return self.post(endpoint, payload=connector_config)

    def get_accounts(self):
        """Get available credentials."""
        endpoint = "list-accounts"
        return self.get(endpoint)

    def get_credentials(self, account_name: str):
        """Get available credentials."""
        endpoint = f"list-credentials/{account_name}"
        return self.get(endpoint)

    def get_accounts_state(self):
        """Get all balances."""
        endpoint = "accounts-state"
        return self.get(endpoint)

    def get_account_state_history(self):
        """Get account state history."""
        endpoint = "account-state-history"
        return self.get(endpoint)
