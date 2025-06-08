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

    def calculate_cash_account_value_excluding_deposits(self) -> dict:
        """
        Calculate cash account value excluding deposits for performance measurement.
        This prevents double-counting when deposits are separately tracked as cash flows in TWR calculations.
        """
        # Get all cash movements
        cash_balance = CashMovementsRepository.get_cash_balance_by_date()

        # Get total deposits to subtract from cash balance
        deposits_raw = CashMovementsRepository.get_cash_deposits_raw()

        # Calculate cumulative deposits by date
        deposits_by_date = {}
        cumulative_deposits = 0.0

        # Sort deposits by date
        sorted_deposits = sorted(deposits_raw, key=lambda x: x['date'])

        for deposit in sorted_deposits:
            deposit_date = deposit['date'].strftime("%Y-%m-%d")
            cumulative_deposits += float(deposit['change'])
            deposits_by_date[deposit_date] = cumulative_deposits

        # Create DataFrame from cash balance data
        df = pd.DataFrame.from_dict(cash_balance)
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df = df.groupby("date", as_index=False).last()
        df = df.sort_values(by="date")
        df.set_index("date", inplace=True)
        df = df.resample("D").ffill()

        # Calculate adjusted cash values excluding deposits
        dataset = {}
        for day, balance in df["balanceTotal"].items():
            day_str = day.strftime("%Y-%m-%d")

            # Find the cumulative deposits up to this date
            cumulative_deposits_to_date = 0.0
            for deposit_date, cum_deposits in deposits_by_date.items():
                if deposit_date <= day_str:
                    cumulative_deposits_to_date = cum_deposits
                else:
                    break

            # Adjust balance by subtracting cumulative deposits
            adjusted_balance = float(balance) - cumulative_deposits_to_date
            dataset[day_str] = max(0.0, adjusted_balance)  # Ensure non-negative

        return dataset
