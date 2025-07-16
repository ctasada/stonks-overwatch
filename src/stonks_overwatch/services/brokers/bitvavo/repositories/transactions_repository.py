from django.db import connection

from stonks_overwatch.utils.database.db_utils import dictfetchall


class TransactionsRepository:
    @staticmethod
    def get_transactions_raw() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_transactions
                """
            )
            return dictfetchall(cursor)
