import glob
import subprocess
import importlib.util
import inspect
import os

from pydantic import BaseModel

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase  # update this to the actual import
import yaml


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


def load_directional_strategies(path):
    strategies = {}
    for filename in os.listdir(path):
        if filename.endswith('.py') and "__init__" not in filename:
            module_name = filename[:-3]  # strip the .py to get the module name
            strategies[module_name] = {"module": module_name}
            file_path = os.path.join(path, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, DirectionalStrategyBase) and cls is not DirectionalStrategyBase:
                    strategies[module_name]["class"] = cls
                if issubclass(cls, BaseModel) and cls is not BaseModel:
                    strategies[module_name]["config"] = cls
    return strategies


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
