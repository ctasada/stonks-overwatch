from django.db import connection

from stonks_overwatch.utils.database.db_utils import dictfetchall


class PositionsRepository:
    @staticmethod
    def get_all_positions() -> list[dict]:
        with connection.cursor() as cursor:
            # In case the date is the same, use the id to provide a consistent sorting
            cursor.execute(
                """
                SELECT *
                FROM ibkr_positions
                ORDER BY conid ASC
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
        with connection.cursor() as cursor:
            # Use a parameterized query to prevent SQL injection
            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"""
                SELECT *
                FROM ibkr_positions
                WHERE conid IN ({placeholders})
                """,
                ids,
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["conid"]: row for row in rows}
        return result_map
