"""Platform detection utilities for cross-platform compatibility."""

import os
from pathlib import Path


def is_flatpak() -> bool:
    """
    Check if the application is running in a Flatpak environment.

    Returns:
        True if running in Flatpak, False otherwise
    """
    # Check multiple indicators of Flatpak environment
    # 1. FLATPAK_ID environment variable
    if os.environ.get("FLATPAK_ID") is not None:
        return True

    # 2. Check for /.flatpak-info file (most reliable)
    if os.path.exists("/.flatpak-info"):
        return True

    # 3. Check container environment variable
    if os.environ.get("container") == "flatpak":
        return True

    # 4. Check if running inside /app directory (Flatpak standard)
    if os.path.exists("/app") and os.path.abspath(__file__).startswith("/app/"):
        return True

    return False


def get_flatpak_paths() -> dict[str, Path]:
    """
    Get application paths for Flatpak environment using XDG directories.

    Returns:
        Dictionary with 'data', 'config', 'logs', and 'cache' paths
    """
    # Get XDG directories, with fallback to defaults
    xdg_data_home_env = os.environ.get("XDG_DATA_HOME")
    xdg_data_home = Path(xdg_data_home_env) if xdg_data_home_env else Path.home() / ".local" / "share"

    xdg_config_home_env = os.environ.get("XDG_CONFIG_HOME")
    xdg_config_home = Path(xdg_config_home_env) if xdg_config_home_env else Path.home() / ".config"

    xdg_cache_home_env = os.environ.get("XDG_CACHE_HOME")
    xdg_cache_home = Path(xdg_cache_home_env) if xdg_cache_home_env else Path.home() / ".cache"

    # Use app name for directory structure
    app_name = "stonks-overwatch"

    return {
        "data": xdg_data_home / app_name,
        "config": xdg_config_home / app_name,
        "logs": xdg_data_home / app_name / "logs",
        "cache": xdg_cache_home / app_name,
    }
