import glob
import subprocess
import importlib.util
import inspect
import os
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingControllerBase, DirectionalTradingControllerConfigBase

import yaml
from hummingbot.smart_components.strategy_frameworks.market_making import MarketMakingControllerBase, \
    MarketMakingControllerConfigBase


def remove_files_from_directory(directory: str):
    for file in os.listdir(directory):
        os.remove(f"{directory}/{file}")


def remove_file(file_path: str):
    os.remove(file_path)


def remove_directory(directory: str):
    process = subprocess.Popen(f"rm -rf {directory}", shell=True)
    process.wait()


def dump_dict_to_yaml(data_dict, filename):
    with open(filename, 'w') as file:
        yaml.dump(data_dict, file)


def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


def directory_exists(directory: str):
    return os.path.exists(directory)


def save_file(name: str, content: str, path: str):
    complete_file_path = os.path.join(path, name)
    os.makedirs(path, exist_ok=True)
    with open(complete_file_path, "w") as file:
        file.write(content)


def load_file(path: str) -> str:
    try:
        with open(path, 'r') as file:
            contents = file.read()
        return contents
    except FileNotFoundError:
        print(f"File '{path}' not found.")
        return ""
    except IOError:
        print(f"Error reading file '{path}'.")
        return ""


def get_directories_from_directory(directory: str) -> list:
    directories = glob.glob(directory + "/**/")
    return directories


def get_python_files_from_directory(directory: str) -> list:
    py_files = glob.glob(directory + "/**/*.py", recursive=True)
    py_files = [path for path in py_files if not path.endswith("__init__.py")]
    return py_files


def get_log_files_from_directory(directory: str) -> list:
    log_files = glob.glob(directory + "/**/*.log*", recursive=True)
    return log_files


def get_yml_files_from_directory(directory: str) -> list:
    yml = glob.glob(directory + "/**/*.yml", recursive=True)
    return yml


def load_controllers(path):
    controllers = {}
    for filename in os.listdir(path):
        if filename.endswith('.py') and "__init__" not in filename:
            module_name = filename[:-3]  # strip the .py to get the module name
            controllers[module_name] = {"module": module_name}
            file_path = os.path.join(path, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, DirectionalTradingControllerBase) and cls is not DirectionalTradingControllerBase:
                    controllers[module_name]["class"] = cls
                    controllers[module_name]["type"] = "directional_trading"
                if issubclass(cls, DirectionalTradingControllerConfigBase) and cls is not DirectionalTradingControllerConfigBase:
                    controllers[module_name]["config"] = cls
                if issubclass(cls, MarketMakingControllerBase) and cls is not MarketMakingControllerBase:
                    controllers[module_name]["class"] = cls
                    controllers[module_name]["type"] = "market_making"
                if issubclass(cls, MarketMakingControllerConfigBase) and cls is not MarketMakingControllerConfigBase:
                    controllers[module_name]["config"] = cls
    return controllers


def get_bots_data_paths():
    root_directory = "hummingbot_files/bots"
    bots_data_paths = {"General / Uploaded data": "data"}
    reserved_word = "hummingbot-"
    # Walk through the directory tree
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for dirname in dirnames:
            if dirname == "data":
                parent_folder = os.path.basename(dirpath)
                if parent_folder.startswith(reserved_word):
                    bots_data_paths[parent_folder] = os.path.join(dirpath, dirname)
            if "dashboard" in bots_data_paths:
                del bots_data_paths["dashboard"]
    data_sources = {key: value for key, value in bots_data_paths.items() if value is not None}
    return data_sources


def get_databases():
    databases = {}
    bots_data_paths = get_bots_data_paths()
    for source_name, source_path in bots_data_paths.items():
        sqlite_files = {}
        for db_name in os.listdir(source_path):
            if db_name.endswith(".sqlite"):
                sqlite_files[db_name] = os.path.join(source_path, db_name)
        databases[source_name] = sqlite_files
    if len(databases) > 0:
        return {key: value for key, value in databases.items() if value}
    else:
        return None


def get_function_from_file(file_path: str, function_name: str):
    # Create a module specification from the file path and load it
    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the function from the module
    function = getattr(module, function_name)
    return function


def execute_bash_command(command: str, shell: bool = True, wait: bool = False):
    process = subprocess.Popen(command, shell=shell)
    if wait:
        process.wait()
