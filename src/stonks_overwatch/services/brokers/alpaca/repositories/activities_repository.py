"""Repository for Alpaca activity data (dividends, deposits, withdrawals)."""

from typing import List

from stonks_overwatch.services.brokers.alpaca.client.constants import DEPOSIT_ACTIVITY_TYPES, DIVIDEND_ACTIVITY_TYPES
from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaActivity


class ActivitiesRepository:
    """Data access layer for AlpacaActivity records."""

    @staticmethod
    def get_dividend_activities() -> List[AlpacaActivity]:
        """
        Retrieve all dividend-related activities.

        Returns:
            List of AlpacaActivity objects for dividend types
        """
        dividend_types = [at.value for at in DIVIDEND_ACTIVITY_TYPES]
        return list(AlpacaActivity.objects.filter(activity_type__in=dividend_types).order_by("-activity_date"))

    @staticmethod
    def get_deposit_activities() -> List[AlpacaActivity]:
        """
        Retrieve all deposit and withdrawal activities.

        Returns:
            List of AlpacaActivity objects for deposit/withdrawal types
        """
        deposit_types = [at.value for at in DEPOSIT_ACTIVITY_TYPES]
        return list(AlpacaActivity.objects.filter(activity_type__in=deposit_types).order_by("-activity_date"))

    @staticmethod
    def get_all_activities() -> List[AlpacaActivity]:
        """
        Retrieve all stored activities.

        Returns:
            List of all AlpacaActivity objects
        """
        return list(AlpacaActivity.objects.all().order_by("-activity_date"))
