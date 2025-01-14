import logging
from datetime import date
from typing import List

import pandas as pd

from stonks_overwatch.config import Config
from stonks_overwatch.services.bitvavo.deposits import DepositsService as BitvavoDepositsService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.deposits import DepositsService as DeGiroDepositsService
from stonks_overwatch.services.models import Deposit
from stonks_overwatch.utils.localization import LocalizationUtility


class DepositsAggregatorService:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")

    def __init__(self):
        self.degiro_service = DeGiroService()

        self.degiro_deposits = DeGiroDepositsService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_deposits = BitvavoDepositsService()

    def cash_deposits_history(self) -> list[dict]:
        cash_contributions = self.get_cash_deposits()
        df = pd.DataFrame.from_dict(cash_contributions)
        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Group by day, adding the values
        df.set_index("date", inplace=True)
        df = df.sort_values(by="date")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cumulative sum
        df["contributed"] = df["change"].cumsum()

        cash_contributions = df.to_dict("records")
        for contribution in cash_contributions:
            contribution["date"] = contribution["date"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["date"],
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

    def get_cash_deposits(self) -> List[Deposit]:
        deposits = []
        if Config.default().is_degiro_enabled():
            deposits += self.degiro_deposits.get_cash_deposits()

        if Config.default().is_bitvavo_enabled():
            deposits += self.bitvavo_deposits.get_cash_deposits()

        deposits = sorted(deposits, key=lambda x: x.date, reverse=True)

        return deposits
