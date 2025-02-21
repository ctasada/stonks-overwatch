from typing import List

import pandas as pd

from stonks_overwatch.config.config import Config
from stonks_overwatch.repositories.degiro.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.models import Deposit, DepositType


# FIXME: If data cannot be found in the DB, the code should get it from DeGiro, updating the DB
class DepositsService:
    def __init__(
            self,
            degiro_service: DeGiroService,
    ):
        self.degiro_service = degiro_service
        self.base_currency = Config.default().base_currency

    def get_cash_deposits(self) -> List[Deposit]:
        df = pd.DataFrame(CashMovementsRepository.get_cash_deposits_raw())

        df = df.sort_values(by="date", ascending=False)

        records = []
        for _, row in df.iterrows():
            records.append(
                Deposit(
                    type=DepositType.DEPOSIT if row["change"] > 0 else DepositType.WITHDRAWAL,
                    datetime=row["date"],
                    description=self._capitalize_deposit_description(row["description"]),
                    change=row["change"],
                    currency=self.base_currency,
                )
            )

        return records

    @staticmethod
    def _capitalize_deposit_description(input_string: str):
        words = input_string.split()
        capitalized_words = [
            word if word == "iDEAL" else word.capitalize() for word in words
        ]
        return " ".join(capitalized_words)

    def calculate_cash_account_value(self) -> dict:
        cash_balance = CashMovementsRepository.get_cash_balance_by_date()

        # Create DataFrame from the fetched data
        df = pd.DataFrame.from_dict(cash_balance)

        # Convert the 'date' column to datetime and remove the time component
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Group by date and take the last balance_total for each day
        df = df.groupby("date", as_index=False).last()

        # Sort values by date (just in case)
        df = df.sort_values(by="date")

        # Set the 'date' column as the index and fill missing dates
        df.set_index("date", inplace=True)
        df = df.resample("D").ffill()

        # Convert the DataFrame to a dictionary with date as the key (converted to string)
        # and balance_total as the value
        dataset = {day.strftime("%Y-%m-%d"): float(balance) for day, balance in df["balanceTotal"].items()}

        return dataset
