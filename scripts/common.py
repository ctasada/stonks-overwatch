# IMPORTATIONS
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

def connect_to_degiro():
    from degiro.services.degiro_service import DeGiroService
    degiro = DeGiroService()

    # CONNECT
    degiro.connect()

    return degiro.get_client()
