import os
import yaml


def remove_files_from_directory(directory: str):
    for file in os.listdir(directory):
        os.remove(f"{directory}/{file}")


def dump_dict_to_yaml(data_dict, filename):
    with open(filename, 'w') as file:
        yaml.dump(data_dict, file)
