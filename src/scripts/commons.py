import json
import os
from typing import Any

IMPORT_FOLDER = './import'
TIME_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
DATE_FORMAT = '%Y-%m-%d'

def init() -> None:
    """
    Executes needed initializations for the scripts.

    * Creates the folder to put the imported files
    ### Returns:
        None
    """
    if not os.path.exists(IMPORT_FOLDER):
        os.makedirs(IMPORT_FOLDER)

def save_to_json(data: Any, json_file_path: str) -> None:
    """
    Saves the data into the specified file using JSON format
    ### Parameters
    * data: Any
        - The data structure we want to save
    * json_file_path: str
        - The file where we want to save the data
    ### Returns:
        None
    """
    data_file = open(json_file_path, 'w')
    data_file.write(json.dumps(data, indent = 4))
    data_file.close()