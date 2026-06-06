"""Repository for Alpaca order data."""

from typing import List

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaOrder


class OrdersRepository:
    """Data access layer for AlpacaOrder records."""

    @staticmethod
    def get_filled_orders() -> List[AlpacaOrder]:
        """
        Retrieve all filled (completed) orders, sorted newest first.

        Returns:
            List of AlpacaOrder objects with status 'filled'
        """
        return list(AlpacaOrder.objects.filter(status="filled").order_by("-filled_at"))

    @staticmethod
    def get_filled_orders_chronological() -> List[AlpacaOrder]:
        """
        Retrieve all filled orders sorted oldest-first.

        This ordering is required for FIFO cost-basis calculations: buys must
        be matched against sells in the order they were originally placed.

        Returns:
            List of AlpacaOrder objects with status 'filled', oldest first
        """
        return list(
            AlpacaOrder.objects.filter(status="filled")
            .exclude(filled_at=None)
            .exclude(filled_avg_price=None)
            .order_by("filled_at")
        )

    @staticmethod
    def get_all_orders() -> List[AlpacaOrder]:
        """
        Retrieve all stored orders.

        Returns:
            List of AlpacaOrder objects
        """
        return list(AlpacaOrder.objects.all().order_by("-submitted_at"))
