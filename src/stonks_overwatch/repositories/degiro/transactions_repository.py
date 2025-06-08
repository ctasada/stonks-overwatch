from datetime import datetime

from django.db import connection

from stonks_overwatch.repositories.degiro.models import DeGiroTransactions
from stonks_overwatch.utils.db_utils import dictfetchall

class TransactionsRepository:
    @staticmethod
    def get_transactions_raw() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_products_transactions() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, product_id, quantity FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_product_transactions(product_ids: list[str]) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM degiro_transactions
                WHERE product_id IN ({", ".join(map(str, product_ids))})
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_portfolio_products(only_open: bool = False) -> list[dict]:
        with connection.cursor() as cursor:
            query = """
                    SELECT product_id,
                           SUM(quantity) AS size,
                           SUM(total_plus_all_fees_in_base_currency) as total_plus_all_fees_in_base_currency,
                           ABS(SUM(total_plus_all_fees_in_base_currency) / SUM(quantity)) AS break_even_price
                    FROM degiro_transactions
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
            date: the latest update from the DB, None if there is no entry
        """
        try:
            entry = DeGiroTransactions.objects.all().order_by("-date").first()
            if entry is not None:
                return entry.date
        except Exception:
            """Ignore. The Database doesn't contain anything"""

        return None
