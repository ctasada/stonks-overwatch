from django.db import connection

from stonks_overwatch.utils.database.db_utils import dictfetchone


class AssetsRepository:
    @staticmethod
    def get_asset(symbol: str) -> dict | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM bitvavo_assets WHERE symbol = %s
                """,
                [symbol],
            )
            return dictfetchone(cursor)
