import os

IMPORT_FOLDER = "./import"
TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DATE_FORMAT = "%Y-%m-%d"


def init() -> None:
    """Execute needed initializations for the scripts.

    * Creates the folder to put the imported files
    ### Returns:
        None
    """
    if not os.path.exists(IMPORT_FOLDER):
        os.makedirs(IMPORT_FOLDER)
