from stonks_overwatch.config import Config
from stonks_overwatch.services.bitvavo.fees import FeesService as BitvavoFeesService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.fees import FeesService as DeGiroFeesService


class FeesAggregatorService:

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_fees = DeGiroFeesService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_fees = BitvavoFeesService()

    def get_fees(self) -> list[dict]:
        fees = []
        if Config.default().is_degiro_enabled():
            fees += self.degiro_fees.get_fees()

        if Config.default().is_bitvavo_enabled():
            fees += self.bitvavo_fees.get_fees()

        return sorted(fees, key=lambda k: (k["date"], k["time"]), reverse=True)
