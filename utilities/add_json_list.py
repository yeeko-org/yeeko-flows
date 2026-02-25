import json
import os


def add_data_to_list(data, file_path='data.json'):

    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    if isinstance(existing_data, list):
        existing_data.append(data)
    else:
        existing_data = [existing_data, data]

    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)
