"""Repository for Alpaca position data."""

from typing import List

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaPosition


class PositionsRepository:
    """Data access layer for AlpacaPosition records."""

    @staticmethod
    def get_all_positions() -> List[AlpacaPosition]:
        """
        Retrieve all stored positions.

        Returns:
            QuerySet of AlpacaPosition objects
        """
        return list(AlpacaPosition.objects.all())

    @staticmethod
    def get_symbols() -> List[str]:
        """
        Retrieve all stored position symbols.

        Returns:
            List of symbol strings
        """
        return list(AlpacaPosition.objects.values_list("symbol", flat=True))
