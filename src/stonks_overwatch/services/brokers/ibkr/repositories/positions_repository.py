from stonks_overwatch.services.brokers.ibkr.repositories.models import IBKRPosition
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model


class PositionsRepository:
    @staticmethod
    def get_all_positions() -> list[dict]:
        connection = get_connection_for_model(IBKRPosition)
        with connection.cursor() as cursor:
            # In case the date is the same, use the id to provide a consistent sorting
            cursor.execute(
                """
                SELECT *
                FROM ibkr_positions
                ORDER BY conid
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_products_info_raw(ids: list[int]) -> dict:
        """Gets product information from the given product id. The information is retrieved from the DB.
        ### Parameters
            * productIds: list of ints
                - The product ids to query
        ### Returns
            list: list of product infos
        """
        connection = get_connection_for_model(IBKRPosition)
        with connection.cursor() as cursor:
            # Use a parameterized query to prevent SQL injection
            placeholders = ",".join(["%s"] * len(ids))
            query = f"""
                SELECT *
                FROM ibkr_positions
                WHERE conid IN ({placeholders})
                """  # nosec: B608 - placeholders are generated safely and values are parameterized
            cursor.execute(query, ids)
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["conid"]: row for row in rows}
        return result_map
