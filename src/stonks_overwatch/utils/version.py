import os

import toml

from settings import PROJECT_PATH


def get_version() -> str:
    pyproject_path = os.path.join(PROJECT_PATH, 'pyproject.toml')
    with open(pyproject_path, 'r') as f:
        pyproject_data = toml.load(f)
    return f"v{pyproject_data['project']['version']}"
