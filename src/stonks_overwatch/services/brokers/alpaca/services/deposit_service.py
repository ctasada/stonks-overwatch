"""Alpaca deposit service implementation."""

from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Optional

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.services.brokers.alpaca.client.constants import ActivityType
from stonks_overwatch.services.brokers.alpaca.repositories.activities_repository import ActivitiesRepository
from stonks_overwatch.services.brokers.alpaca.services.alpaca_base_service import AlpacaBaseService
from stonks_overwatch.services.models import Deposit, DepositType
from stonks_overwatch.utils.core.logger import StonksLogger


class DepositService(AlpacaBaseService, DepositServiceInterface):
    """
    Deposit service for Alpaca Markets.

    Reads deposit and withdrawal activities (CSD, CSW, TRANS, JNLC, JNL) from
    the local DB and maps them to the shared Deposit model.  All Alpaca
    net_amount values are denominated in USD; amounts are converted to the
    user's base_currency using the historical exchange rate for each
    activity's date before being stored on the Deposit object.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.deposit", "[ALPACA|DEPOSIT]")

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the deposit service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
        """
        super().__init__(config)

    def get_cash_deposits(self) -> List[Deposit]:
        """
        Retrieve deposit and withdrawal records converted to base_currency.

        Each activity's net_amount (USD) is converted to the user's base
        currency using the historical rate for that activity's date.

        Returns:
            List of Deposit objects sorted newest first
        """
        self.logger.debug("Getting Alpaca cash deposits")
        activities = ActivitiesRepository.get_deposit_activities()
        deposits: List[Deposit] = []

        for activity in activities:
            net_amount_usd = float(activity.net_amount or 0)
            activity_date = activity.activity_date

            if activity_date:
                dt = datetime(activity_date.year, activity_date.month, activity_date.day, tzinfo=dt_timezone.utc)
            else:
                dt = datetime.now(tz=dt_timezone.utc)
                activity_date = dt.date()

            converted_amount = self._to_base(net_amount_usd, on_date=activity_date)

            # CSD is always a deposit by definition; for other types use the sign.
            deposit_type = (
                DepositType.DEPOSIT
                if activity.activity_type == ActivityType.CSD.value or net_amount_usd >= 0
                else DepositType.WITHDRAWAL
            )

            try:
                activity_label = ActivityType(activity.activity_type).label
            except ValueError:
                activity_label = activity.activity_type

            deposits.append(
                Deposit(
                    datetime=dt,
                    type=deposit_type,
                    change=converted_amount,
                    currency=self.base_currency,
                    description=activity.description or activity_label,
                )
            )

        return deposits

    def calculate_cash_account_value(self) -> Dict[str, float]:
        """
        Calculate the cumulative cash account value over time.

        Amounts are already converted to base_currency by get_cash_deposits(),
        so the running total is in the user's base currency.

        Returns:
            Dictionary mapping date strings to cumulative cash values in base_currency
        """
        self.logger.debug("Calculating Alpaca cash account value")
        deposits = self.get_cash_deposits()
        deposits_sorted = sorted(deposits, key=lambda d: d.datetime)

        cash_account: Dict[str, float] = {}
        running_total = 0.0

        for deposit in deposits_sorted:
            date_key = deposit.datetime_as_date()
            running_total += deposit.change
            cash_account[date_key] = running_total

        return cash_account
