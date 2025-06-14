import json
from typing import Any


def save_to_json(data: Any, json_file_path: str) -> None:
    """Save the data into the specified file using JSON format.

    ### Parameters
    * data: Any
        - The data structure we want to save
    * json_file_path: str
        - The file where we want to save the data
    ### Returns:
        None
    """
    with open(json_file_path, "w") as data_file:
        data_file.write(json.dumps(data, indent=4))


def load_from_json(json_file_path: str) -> Any:
    """Load the data from the specified file using JSON format.

    ### Parameters
    * json_file_path: str
        - The file where we want to load the data from
    ### Returns:
        None
    """
    with open(json_file_path, "r") as data_file:
        data = json.load(data_file)
    return data
