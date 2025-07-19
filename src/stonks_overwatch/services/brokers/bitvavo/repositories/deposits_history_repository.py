from django.db import connection

from stonks_overwatch.utils.database.db_utils import dictfetchall


class DepositsHistoryRepository:
    @staticmethod
    def get_deposits_history_raw() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_deposit_history
                """
            )
            return dictfetchall(cursor)
