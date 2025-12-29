from typing import Dict, List

from currency_converter import CurrencyConverter
from django.utils import timezone

from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.models import Deposit, DepositType
from stonks_overwatch.utils.core.logger import StonksLogger


class DepositService(BaseService, DepositServiceInterface):
    """
    Metatrader4 Deposit Service.

    This service retrieves deposit and withdrawal data from Metatrader4 balance entries.
    Balance entries in MT4 represent cash deposits, withdrawals, and other account adjustments.
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|DEPOSIT]")
        self.repository = Metatrader4Repository()
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.account_currency = self.repository.get_account_currency()

    def get_cash_deposits(self) -> List[Deposit]:
        """
        Retrieves the cash deposit and withdrawal history from balance entries.

        Returns:
            List[Deposit]: List of deposits and withdrawals sorted by date (newest first)
        """
        self.logger.debug("Fetching deposit data from database")

        try:
            # Get balance entries from the database
            balance_entries = self.repository.get_balance_entries()

            deposits = []

            for trade in balance_entries:
                try:
                    deposit = self._create_deposit(trade)
                    # Skip deposits with None datetime (shouldn't happen but safety check)
                    if deposit.datetime is None:
                        self.logger.warning(f"Skipping deposit with None datetime from trade {trade.ticket}")
                        continue
                    deposits.append(deposit)
                except Exception as e:
                    self.logger.warning(f"Failed to create deposit from trade: {trade}, error: {e}")
                    continue

            # Sort by date descending (newest first) - should work now with consistent timezone handling
            deposits.sort(key=lambda d: d.datetime, reverse=True)

            self.logger.debug(f"Retrieved {len(deposits)} deposits from database")
            return deposits

        except Exception as e:
            self.logger.error(f"Failed to get deposits from database: {e}")
            raise

    def calculate_cash_account_value(self) -> Dict[str, float]:
        """
        Calculates the cash account value over time based on deposit history.

        Returns:
            Dict[str, float]: Dictionary mapping date strings (YYYY-MM-DD) to cash balance values
        """
        self.logger.debug("Calculating cash account value over time")

        try:
            deposits = self.get_cash_deposits()

            # Sort deposits by date ascending (oldest first) for cumulative calculation
            deposits.sort(key=lambda d: d.datetime)

            cash_values = {}
            running_balance = 0.0

            for deposit in deposits:
                # Add deposit amount to running balance
                running_balance += deposit.change

                # Store the balance for this date
                date_str = deposit.datetime_as_date()
                cash_values[date_str] = running_balance

            self.logger.debug(f"Calculated cash values for {len(cash_values)} dates")
            return cash_values

        except Exception as e:
            self.logger.error(f"Failed to calculate cash account value: {e}")
            raise

    def _create_deposit(self, trade) -> Deposit:
        """
        Create a Deposit object from a Metatrader4Trade balance entry.

        Args:
            trade: Metatrader4Trade object with type='balance'

        Returns:
            Deposit: Deposit object representing the balance change
        """
        # Determine deposit type based on profit value
        profit = float(trade.profit or 0)
        deposit_type = DepositType.DEPOSIT if profit > 0 else DepositType.WITHDRAWAL

        # Convert profit from account currency to base currency
        if self.account_currency != self.base_currency:
            profit = self.currency_converter.convert(
                profit,
                self.account_currency,
                self.base_currency,
            )

        # Use open_time as the transaction datetime (balance entries use open_time)
        transaction_datetime = trade.open_time

        # Handle None datetime case
        if transaction_datetime is None:
            self.logger.warning(f"Trade {trade.ticket} has no open_time, using current time")
            transaction_datetime = timezone.now()
        else:
            # Ensure datetime is timezone-aware using Django's default timezone
            # The repository should already handle this, but add safety check
            if transaction_datetime.tzinfo is None:
                transaction_datetime = timezone.make_aware(transaction_datetime)

        # Use description if available, otherwise create a default description
        description = trade.description or f"Balance adjustment - {deposit_type.value}"

        return Deposit(
            datetime=transaction_datetime,
            type=deposit_type,
            change=profit,
            currency=self.base_currency,
            description=description,
        )
