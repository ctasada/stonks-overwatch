import os

# Import platform utilities (safe - only uses standard library, no Django imports)
from stonks_overwatch.utils.platform_utils import get_flatpak_paths, is_flatpak


def _setup_environment():
    """Set up environment variables before any imports that might use them."""
    # Set app indicator
    os.environ["STONKS_OVERWATCH_APP"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "stonks_overwatch.settings"

    # Check if running in Flatpak and set paths early
    if is_flatpak():
        flatpak_paths = get_flatpak_paths()
        os.environ["STONKS_OVERWATCH_DATA_DIR"] = flatpak_paths["data"].as_posix()
        os.environ["STONKS_OVERWATCH_CONFIG_DIR"] = flatpak_paths["config"].as_posix()
        os.environ["STONKS_OVERWATCH_LOGS_DIR"] = flatpak_paths["logs"].as_posix()
        os.environ["STONKS_OVERWATCH_CACHE_DIR"] = flatpak_paths["cache"].as_posix()

        # Create directories immediately to prevent FileNotFoundError
        for path in flatpak_paths.values():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we can't create the directory, we'll handle it later
                pass


# CRITICAL: Set up environment variables BEFORE importing anything else
_setup_environment()

# NOW it's safe to import the app
from stonks_overwatch.app import main  # noqa: E402

if __name__ == "__main__":
    main().main_loop()
