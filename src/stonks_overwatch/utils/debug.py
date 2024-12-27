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
    data_file = open(json_file_path, "w")
    data_file.write(json.dumps(data, indent=4))
    data_file.close()
