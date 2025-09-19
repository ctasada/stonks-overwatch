# IMPORTATIONS
import logging

from scripts.common import setup_django_environment

setup_django_environment()

# Initialize broker registry for standalone script usage
from stonks_overwatch.core.registry_setup import ensure_registry_initialized  # noqa: E402

ensure_registry_initialized()

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)


def connect_to_degiro():
    from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

    degiro = DeGiroService(force=True)

    # CONNECT
    degiro.connect()

    return degiro.get_client()
