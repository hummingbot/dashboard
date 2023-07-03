import os
import subprocess

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
