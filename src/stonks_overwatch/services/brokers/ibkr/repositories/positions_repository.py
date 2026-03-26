from stonks_overwatch.services.brokers.ibkr.repositories.models import IBKRPosition
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model, snake_to_camel


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
        if not ids:
            return {}

        rows = [
            {snake_to_camel(key): value for key, value in row.items()}
            for row in IBKRPosition.objects.filter(conid__in=ids).values()
        ]

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["conid"]: row for row in rows}
        return result_map
