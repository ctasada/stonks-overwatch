import logging
import os
import sys


def setup_python_path():
    """Add the src directory to Python path.

    This allows scripts to import from the stonks_overwatch package
    without requiring Django setup.

    Returns:
        None
    """
    # Add the src directory to the Python path
    src_path = os.path.join(os.path.dirname(__file__), "..", "src")
    if src_path not in sys.path:
        sys.path.append(src_path)


def setup_django_environment():
    """Set up Django environment for scripts.

    This function handles:
    1. Adding the src directory to Python path
    2. Setting Django settings module
    3. Initializing Django
    4. Setting up broker registry

    Returns:
        None
    """
    # Ensure Python path is set up first
    setup_python_path()

    # Set up Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stonks_overwatch.settings")

    import django

    django.setup()

    # Initialize broker registry for standalone script usage
    try:
        from stonks_overwatch.core.registry_setup import ensure_registry_initialized

        ensure_registry_initialized()
    except ImportError:
        # Registry setup might not be available in all contexts
        pass


def init_logger() -> None:
    """Execute the necessary initializations for the scripts.
    ### Returns:
        None
    """
    # Configure logging for the stonks_overwatch module
    stonks_overwatch_logger = logging.getLogger("stonks_overwatch")
    stonks_overwatch_logger.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the console handler
    _format = "%(levelname)s %(asctime)s %(module)s %(message)s"
    formatter = logging.Formatter(_format)
    console_handler.setFormatter(formatter)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format=_format)


def setup_script_environment():
    """Complete script setup including Django and logging.

    This is a convenience function that sets up both Django environment
    and logging for scripts that need both.

    Returns:
        None
    """
    setup_django_environment()
    init_logger()
