from datetime import datetime

from stonks_overwatch.services.brokers.ibkr.repositories.models import IBKRTransactions
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model, snake_to_camel


class TransactionsRepository:
    @staticmethod
    def get_transactions_raw() -> list[dict]:
        connection = get_connection_for_model(IBKRTransactions)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM ibkr_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_products_transactions() -> list[dict]:
        connection = get_connection_for_model(IBKRTransactions)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, product_id, quantity FROM ibkr_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_product_transactions(conids: list[int]) -> list[dict]:
        if not conids:
            return []

        return [
            {snake_to_camel(key): value for key, value in row.items()}
            for row in IBKRTransactions.objects.filter(conid__in=conids).values()
        ]

    @staticmethod
    def get_portfolio_products(only_open: bool = False) -> list[dict]:
        connection = get_connection_for_model(IBKRTransactions)
        with connection.cursor() as cursor:
            query = """
                    SELECT product_id,
                           SUM(quantity) AS size,
                           SUM(total_plus_all_fees_in_base_currency) as total_plus_all_fees_in_base_currency,
                           ABS(SUM(total_plus_all_fees_in_base_currency) / SUM(quantity)) AS break_even_price
                    FROM ibkr_transactions
                    GROUP BY product_id
                    """
            if only_open:
                query += "\nHAVING SUM(quantity) > 0"
            cursor.execute(query)
            return dictfetchall(cursor)

    @staticmethod
    def get_last_movement() -> datetime | None:
        """Return the latest update from the DB.

        ### Returns:
            date: the latest update from the DB, None if there is no entry.
        """
        try:
            entry = IBKRTransactions.objects.all().order_by("-date").first()
            if entry is not None:
                return entry.date
        except Exception:
            pass  # Ignore. The Database doesn't contain anything

        return None
