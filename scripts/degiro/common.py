# IMPORTATIONS
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

def connect_to_degiro():
    from stonks_overwatch.services.degiro.degiro_service import DeGiroService
    degiro = DeGiroService(force=True)

    # CONNECT
    degiro.connect()

    return degiro.get_client()
