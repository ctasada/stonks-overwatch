# IMPORTATIONS
import logging
import os
import sys
from pathlib import Path

import django

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stonks_overwatch.settings")
django.setup()

# Initialize broker registry for standalone script usage
from stonks_overwatch.core.registry_setup import ensure_unified_registry_initialized  # noqa: E402

ensure_unified_registry_initialized()

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)


def connect_to_degiro():
    from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

    degiro = DeGiroService(force=True)

    # CONNECT
    degiro.connect()

    return degiro.get_client()
