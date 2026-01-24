from typing import List, Optional

import polars as pl

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.models import Deposit, DepositType
from stonks_overwatch.utils.core.logger import StonksLogger


# FIXME: If data cannot be found in the DB, the code should get it from DeGiro, updating the DB
class DepositsService(BaseService, DepositServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data.degiro", "[DEGIRO|DEPOSITS]")

    def __init__(
        self,
        config: Optional[BaseConfig] = None,
    ):
        super().__init__(config)

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_cash_deposits(self) -> List[Deposit]:
        self.logger.debug("Get Cash Deposits")
        raw_data = CashMovementsRepository.get_cash_deposits_raw()

        if not raw_data:
            return []

        df = pl.DataFrame(raw_data)
        df = df.sort("date", descending=True)

        records = []
        for row in df.iter_rows(named=True):
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
        capitalized_words = [word if word == "iDEAL" else word.capitalize() for word in words]
        return " ".join(capitalized_words)

    def calculate_cash_account_value(self) -> dict:
        cash_balance = CashMovementsRepository.get_cash_balance_by_date()

        if not cash_balance:
            return {}

        # Create DataFrame from the fetched data
        df = pl.DataFrame(cash_balance)

        # Convert the 'date' column to datetime and remove the time component
        df = df.with_columns(pl.col("date").dt.date().alias("date_only"))

        # Group by date and take the last balance_total for each day
        df = df.group_by("date_only").last()

        # Sort values by date
        df = df.sort("date_only")

        # Generate complete date range and fill missing dates
        if len(df) > 0:
            min_date = df.select("date_only").min().item()
            max_date = df.select("date_only").max().item()

            # Create complete date range
            date_range = pl.date_range(min_date, max_date, interval="1d", eager=True)
            complete_dates_df = pl.DataFrame({"date_only": date_range})

            # Join and forward fill
            df = complete_dates_df.join(df, on="date_only", how="left")
            df = df.fill_null(strategy="forward")

        # Convert to dictionary
        dataset = {}
        for row in df.iter_rows(named=True):
            day_str = row["date_only"].strftime("%Y-%m-%d")
            balance = float(row["balanceTotal"]) if row["balanceTotal"] is not None else 0.0
            dataset[day_str] = balance

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
        sorted_deposits = sorted(deposits_raw, key=lambda x: x["date"])

        for deposit in sorted_deposits:
            deposit_date = deposit["date"].strftime("%Y-%m-%d")
            cumulative_deposits += float(deposit["change"])
            deposits_by_date[deposit_date] = cumulative_deposits

        # Create DataFrame from cash balance data
        if not cash_balance:
            return {}

        df = pl.DataFrame(cash_balance)
        df = df.with_columns(pl.col("date").dt.date().alias("date_only"))
        df = df.group_by("date_only").last()
        df = df.sort("date_only")

        # Generate complete date range and fill missing dates
        if len(df) > 0:
            min_date = df.select("date_only").min().item()
            max_date = df.select("date_only").max().item()

            # Create complete date range
            date_range = pl.date_range(min_date, max_date, interval="1d", eager=True)
            complete_dates_df = pl.DataFrame({"date_only": date_range})

            # Join and forward fill
            df = complete_dates_df.join(df, on="date_only", how="left")
            df = df.fill_null(strategy="forward")

        # Calculate adjusted cash values excluding deposits
        dataset = {}
        for row in df.iter_rows(named=True):
            day_str = row["date_only"].strftime("%Y-%m-%d")
            balance = float(row["balanceTotal"]) if row["balanceTotal"] is not None else 0.0

            # Find the cumulative deposits up to this date
            cumulative_deposits_to_date = 0.0
            for deposit_date, cum_deposits in deposits_by_date.items():
                if deposit_date <= day_str:
                    cumulative_deposits_to_date = cum_deposits
                else:
                    break

            # Adjust balance by subtracting cumulative deposits
            adjusted_balance = balance - cumulative_deposits_to_date
            dataset[day_str] = max(0.0, adjusted_balance)  # Ensure non-negative

        return dataset
