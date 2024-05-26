import pandas as pd
import requests
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


class BackendAPIClient:
    """
    This class is a client to interact with the backend API. The Backend API is a REST API that provides endpoints to
    create new Hummingbot instances, start and stop them, add new script and controller config files, and get the status
    of the active bots.
    """
    _shared_instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "MarketsRecorder":
        if cls._shared_instance is None:
            cls._shared_instance = BackendAPIClient(*args, **kwargs)
        return cls._shared_instance

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"

    def is_docker_running(self):
        """Check if Docker is running."""
        url = f"{self.base_url}/is-docker-running"
        response = requests.get(url)
        return response.json()

    def pull_image(self, image_name: str):
        """Pull a Docker image."""
        url = f"{self.base_url}/pull-image/"
        payload = {"image_name": image_name}
        response = requests.post(url, json=payload)
        return response.json()

    def list_available_images(self, image_name: str):
        """List available images by name."""
        url = f"{self.base_url}/available-images/{image_name}"
        response = requests.get(url)
        return response.json()

    def list_active_containers(self):
        """List all active containers."""
        url = f"{self.base_url}/active-containers"
        response = requests.get(url)
        return response.json()

    def list_exited_containers(self):
        """List all exited containers."""
        url = f"{self.base_url}/exited-containers"
        response = requests.get(url)
        return response.json()

    def clean_exited_containers(self):
        """Clean up exited containers."""
        url = f"{self.base_url}/clean-exited-containers"
        response = requests.post(url)
        return response.json()

    def remove_container(self, container_name: str, archive_locally: bool = True, s3_bucket: str = None):
        """Remove a specific container."""
        url = f"{self.base_url}/remove-container/{container_name}"
        params = {"archive_locally": archive_locally}
        if s3_bucket:
            params["s3_bucket"] = s3_bucket
        response = requests.post(url, params=params)
        return response.json()

    def stop_container(self, container_name: str):
        """Stop a specific container."""
        url = f"{self.base_url}/stop-container/{container_name}"
        response = requests.post(url)
        return response.json()

    def start_container(self, container_name: str):
        """Start a specific container."""
        url = f"{self.base_url}/start-container/{container_name}"
        response = requests.post(url)
        return response.json()

    def create_hummingbot_instance(self, instance_config: dict):
        """Create a new Hummingbot instance."""
        url = f"{self.base_url}/create-hummingbot-instance"
        response = requests.post(url, json=instance_config)
        return response.json()

    def start_bot(self, start_bot_config: dict):
        """Start a Hummingbot bot."""
        url = f"{self.base_url}/start-bot"
        response = requests.post(url, json=start_bot_config)
        return response.json()

    def stop_bot(self, bot_name: str, skip_order_cancellation: bool = False, async_backend: bool = True):
        """Stop a Hummingbot bot."""
        url = f"{self.base_url}/stop-bot"
        response = requests.post(url, json={"bot_name": bot_name, "skip_order_cancellation": skip_order_cancellation, "async_backend": async_backend})
        return response.json()

    def import_strategy(self, strategy_config: dict):
        """Import a trading strategy to a bot."""
        url = f"{self.base_url}/import-strategy"
        response = requests.post(url, json=strategy_config)
        return response.json()

    def get_bot_status(self, bot_name: str):
        """Get the status of a bot."""
        url = f"{self.base_url}/get-bot-status/{bot_name}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "data": "Bot not found"}

    def get_bot_history(self, bot_name: str):
        """Get the historical data of a bot."""
        url = f"{self.base_url}/get-bot-history/{bot_name}"
        response = requests.get(url)
        return response.json()

    def get_active_bots_status(self):
        """
        Retrieve the cached status of all active bots.
        Returns a JSON response with the status and data of active bots.
        """
        url = f"{self.base_url}/get-active-bots-status"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()  # Successful request
        else:
            return {"status": "error", "data": "No active bots found"}

    def get_all_controllers_config(self):
        """Get all controller configurations."""
        url = f"{self.base_url}/all-controller-configs"
        response = requests.get(url)
        return response.json()

    def get_available_credentials(self):
        """Get available credentials."""
        url = f"{self.base_url}/list-credentials"
        response = requests.get(url)
        return response.json()

    def get_available_images(self, image_name: str = "hummingbot"):
        """Get available images."""
        url = f"{self.base_url}/available-images/{image_name}"
        response = requests.get(url)
        return response.json()["available_images"]

    def add_script_config(self, script_config: dict):
        """Add a new script configuration."""
        url = f"{self.base_url}/add-script-config"
        response = requests.post(url, json=script_config)
        return response.json()

    def add_controller_config(self, controller_config: dict):
        """Add a new controller configuration."""
        url = f"{self.base_url}/add-controller-config"
        config = {
            "name": controller_config["id"],
            "content": controller_config
        }
        response = requests.post(url, json=config)
        return response.json()

    def get_real_time_candles(self, connector: str, trading_pair: str, interval: str, max_records: int):
        """Get candles data."""
        url = f"{self.base_url}/real-time-candles"
        payload = {
            "connector": connector,
            "trading_pair": trading_pair,
            "interval": interval,
            "max_records": max_records
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_historical_candles(self, connector: str, trading_pair: str, interval: str, start_time: int, end_time: int):
        """Get historical candles data."""
        url = f"{self.base_url}/historical-candles"
        payload = {
            "connector": connector,
            "trading_pair": trading_pair,
            "interval": interval,
            "start_time": start_time,
            "end_time": end_time
        }
        response = requests.post(url, json=payload)
        return response.json()

    def run_backtesting(self, start_time: int, end_time: int, backtesting_resolution: str, trade_cost: float, config: dict):
        """Run backtesting."""
        url = f"{self.base_url}/run-backtesting"
        payload = {
            "start_time": start_time,
            "end_time": end_time,
            "backtesting_resolution": backtesting_resolution,
            "trade_cost": trade_cost,
            "config": config
        }
        response = requests.post(url, json=payload)
        backtesting_results = response.json()
        return {
            "processed_data": pd.DataFrame(backtesting_results["processed_data"]),
            "executors": [ExecutorInfo(**executor) for executor in backtesting_results["executors"]],
            "results": backtesting_results["results"]
        }

    def get_all_configs_from_bot(self, bot_name: str):
        """Get all configurations from a bot."""
        url = f"{self.base_url}/all-controller-configs/bot/{bot_name}"
        response = requests.get(url)
        return response.json()

    def stop_controller_from_bot(self, bot_name: str, controller_id: str):
        """Stop a controller from a bot."""
        config = {"manual_kill_switch": True}
        url = f"{self.base_url}/update-controller-config/bot/{bot_name}/{controller_id}"
        response = requests.post(url, json=config)
        return response.json()

    def start_controller_from_bot(self, bot_name: str, controller_id: str):
        """Start a controller from a bot."""
        config = {"manual_kill_switch": False}
        url = f"{self.base_url}/update-controller-config/bot/{bot_name}/{controller_id}"
        response = requests.post(url, json=config)
        return response.json()
