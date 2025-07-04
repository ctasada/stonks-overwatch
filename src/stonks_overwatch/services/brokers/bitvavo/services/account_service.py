from datetime import datetime
from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.models import AccountOverview
from stonks_overwatch.utils.core.logger import StonksLogger


class AccountOverviewService:
    logger = StonksLogger.get_logger("stonks_overwatch.account_overview_data", "[BITVAVO|ACCOUNT_OVERVIEW]")
    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self):
        self.bitvavo_service = BitvavoService()
        self.base_currency = Config.get_global().base_currency

    def get_account_overview(self) -> List[AccountOverview]:
        self.logger.debug("Get Account Overview")
        # FETCH DATA
        account_history = self.bitvavo_service.account_history()

        # DISPLAY PRODUCTS_INFO
        overview = []
        for item in account_history["items"]:
            asset = self.bitvavo_service.assets(item["receivedCurrency"])

            if item["type"] == "deposit":
                change = float(item["receivedAmount"]) + float(item.get("feesAmount", 0.0))
                currency = item["receivedCurrency"]
            else:
                change = -1 * (float(item.get("sentAmount", 0.0)) + float(item.get("feesAmount", 0.0)))
                currency = item.get("sentCurrency", self.base_currency)

            overview.append(
                AccountOverview(
                    datetime=AccountOverviewService.parse_datetime(item["executedAt"]),
                    value_datetime=AccountOverviewService.parse_datetime(item["executedAt"]),
                    stock_name=asset["name"],
                    stock_symbol=item["receivedCurrency"],
                    description=self.__get_description(item),
                    type=item["type"],
                    currency=currency,
                    change=change,
                )
            )

        return overview

    @staticmethod
    def parse_datetime(value: str) -> datetime:
        """
        Parses a date time string to datetime object.
        """
        return datetime.strptime(value, AccountOverviewService.TIME_DATE_FORMAT)

    @staticmethod
    def __get_description(item: dict) -> str:
        """
        Returns a description of the transaction.
        """
        if item["type"] == "buy":
            change = float(item.get("sentAmount", 0.0)) + float(item.get("feesAmount", 0.0))
            return f"Bought {item['receivedAmount']} {item['receivedCurrency']} for {change} {item['sentCurrency']}"
        elif item["type"] == "staking":
            return f"Staking {item['receivedAmount']} {item['receivedCurrency']}"
        else:
            return item["type"].title()
