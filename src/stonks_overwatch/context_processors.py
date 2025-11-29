import functools
import os
import tomllib
from pathlib import Path

from django.http import HttpRequest


def app_mode_processor(request: HttpRequest) -> dict[str, bool]:
    """Add app mode context to detect if running in Toga WebView or as webapp"""
    is_desktop_app = os.environ.get("STONKS_OVERWATCH_APP") == "1"
    return {
        "is_desktop_app": is_desktop_app,
        "is_webapp": not is_desktop_app,
    }


def _get_project_version() -> str:
    """Read version from pyproject.toml (webapp mode)."""
    # Calculate project root (same logic as settings.py)
    base_dir = Path(__file__).resolve().parent  # src/stonks_overwatch/
    project_path = base_dir.parent.parent  # project root
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                return pyproject_data.get("project", {}).get("version", "Unknown Version")
        except Exception:
            pass
    return "Unknown Version"


@functools.lru_cache(maxsize=1)
def get_cached_project_version() -> str:
    return _get_project_version()


def version_processor(request: HttpRequest) -> dict[str, str]:
    """Add application version to template context."""
    is_desktop_app = os.environ.get("STONKS_OVERWATCH_APP") == "1"
    if is_desktop_app:
        version = os.environ.get("STONKS_OVERWATCH_VERSION", "Unknown Version")
    else:
        version = get_cached_project_version()
    return {"VERSION": version}
