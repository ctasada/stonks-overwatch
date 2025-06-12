from datetime import date
from typing import List

import pandas as pd

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService as BitvavoDepositsService
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.services.deposit_service import DepositsService as DeGiroDepositsService
from stonks_overwatch.services.models import Deposit, PortfolioId
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger

class DepositsAggregatorService:
    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data", "[AGGREGATOR|DEPOSITS]")

    def __init__(self):
        self.degiro_service = DeGiroService()

        self.degiro_deposits = DeGiroDepositsService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_deposits = BitvavoDepositsService()

    def cash_deposits_history(self, selected_portfolio: PortfolioId) -> list[dict]:
        cash_contributions = self.get_cash_deposits(selected_portfolio)
        df = pd.DataFrame.from_dict(cash_contributions)

        # Group by day, adding the values
        df.set_index("datetime", inplace=True)
        df = df.sort_values(by="datetime")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cumulative sum
        df["contributed"] = df["change"].cumsum()

        cash_contributions = df.to_dict("records")
        for contribution in cash_contributions:
            contribution["datetime"] = contribution["datetime"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["datetime"],
                    "total_deposit": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "date": LocalizationUtility.format_date_from_date(date.today()),
                "total_deposit": cash_contributions[-1]["contributed"],
            }
        )

        return dataset

    def get_cash_deposits(self, selected_portfolio: PortfolioId) -> List[Deposit]:
        deposits = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            deposits += self.degiro_deposits.get_cash_deposits()

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            deposits += self.bitvavo_deposits.get_cash_deposits()

        deposits = sorted(deposits, key=lambda x: x.datetime, reverse=True)

        return deposits
