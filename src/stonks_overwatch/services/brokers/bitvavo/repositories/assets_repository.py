from stonks_overwatch.services.brokers.bitvavo.repositories.models import BitvavoAssets
from stonks_overwatch.utils.database.db_utils import dictfetchone, get_connection_for_model


class AssetsRepository:
    @staticmethod
    def get_asset(symbol: str) -> dict | None:
        connection = get_connection_for_model(BitvavoAssets)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM bitvavo_assets WHERE symbol = %s
                """,
                [symbol],
            )
            return dictfetchone(cursor)
