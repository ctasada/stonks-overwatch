from django.db import connection

from degiro.utils.db_utils import dictfetchall


class TransactionsRepository:
    def get_transactions_raw(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)
