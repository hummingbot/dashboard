import glob
import subprocess
import importlib.util
import inspect
import os
from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase  # update this to the actual import
import yaml


def remove_files_from_directory(directory: str):
    for file in os.listdir(directory):
        os.remove(f"{directory}/{file}")


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


def get_python_files_from_directory(directory: str) -> list:
    py_files = glob.glob(directory + "/**/*.py", recursive=True)
    py_files = [path for path in py_files if not path.endswith("__init__.py")]
    return py_files


def load_directional_strategies(path):
    strategy_classes = []
    for filename in os.listdir(path):
        if filename.endswith('.py'):
            module_name = filename[:-3]  # strip the .py to get the module name
            file_path = os.path.join(path, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, DirectionalStrategyBase) and cls is not DirectionalStrategyBase:
                    strategy_classes.append(cls)
    return strategy_classes

