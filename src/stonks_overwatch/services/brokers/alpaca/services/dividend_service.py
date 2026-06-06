"""Alpaca dividend service implementation."""

from datetime import datetime, timezone as dt_timezone
from typing import List, Optional

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.services.brokers.alpaca.repositories.activities_repository import ActivitiesRepository
from stonks_overwatch.services.brokers.alpaca.services.alpaca_base_service import AlpacaBaseService
from stonks_overwatch.services.models import Dividend, DividendType
from stonks_overwatch.utils.core.logger import StonksLogger


class DividendService(AlpacaBaseService, DividendServiceInterface):
    """
    Dividend service for Alpaca Markets.

    Reads dividend activities (DIV, DIVCGL, DIVCGS, DIVFT, DIVNRA, DIVROC,
    DIVTXEX) from the local DB and maps them to the shared Dividend model.
    All amounts from Alpaca are in USD and are converted to base_currency using
    the historical exchange rate on each activity's date.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.dividend", "[ALPACA|DIVIDEND]")

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the dividend service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
        """
        super().__init__(config)

    def get_dividends(self) -> List[Dividend]:
        """
        Retrieve dividend payment records.

        Maps Alpaca activity types to DividendType:
        - DIV, DIVCGL, DIVCGS, DIVROC, DIVTXEX → PAID
        - DIVFT, DIVNRA → amounts treated as taxes withheld (stored as negative net)

        All amounts are converted from USD to base_currency at the historical
        rate for each activity's date.

        Returns:
            List of Dividend objects sorted newest first
        """
        self.logger.debug("Getting Alpaca dividends")
        activities = ActivitiesRepository.get_dividend_activities()
        dividends: List[Dividend] = []

        for activity in activities:
            net_amount = float(activity.net_amount or 0)
            activity_date = activity.activity_date

            if activity_date:
                dt = datetime(activity_date.year, activity_date.month, activity_date.day, tzinfo=dt_timezone.utc)
            else:
                dt = datetime.now(tz=dt_timezone.utc)

            # Foreign tax withheld and NRA withheld are negative amounts (tax deductions).
            # Convert each value individually at the activity's historical rate.
            taxes = 0.0
            amount = self._to_base(net_amount, on_date=activity_date)
            if activity.activity_type in ("DIVFT", "DIVNRA"):
                taxes = abs(amount)
                amount = 0.0

            dividends.append(
                Dividend(
                    dividend_type=DividendType.PAID,
                    payment_date=dt,
                    stock_name=activity.symbol or "",
                    stock_symbol=activity.symbol or "",
                    currency=self.base_currency,
                    amount=amount,
                    taxes=taxes,
                )
            )

        return sorted(dividends, key=lambda d: d.payment_date, reverse=True)
