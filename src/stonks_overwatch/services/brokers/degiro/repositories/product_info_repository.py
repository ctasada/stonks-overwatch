from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductInfo
from stonks_overwatch.utils.database.db_utils import dictfetchall, dictfetchone, get_connection_for_model


class ProductInfoRepository:
    @staticmethod
    def get_products_info_raw(ids: list[int]) -> dict:
        """Gets product information from the given product id. The information is retrieved from the DB.
        ### Parameters
            * productIds: list of ints
                - The product ids to query
        ### Returns
            list: list of product infos
        """
        connection = get_connection_for_model(DeGiroProductInfo)
        with connection.cursor() as cursor:
            # Use a parameterized query to prevent SQL injection
            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE id IN ({placeholders})
                """,  # nosec B608
                ids,
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["id"]: row for row in rows}
        return result_map

    @staticmethod
    def get_products_info_raw_by_symbol(symbols: list[str]) -> dict:
        """Gets product information from the given symbol. The information is retrieved from the DB.
        ### Parameters
            * symbols: list of str
                - The product symbols to query
        ### Returns
            list: list of product infos. For a single symbol, the list may contain multiple products.
        """
        connection = get_connection_for_model(DeGiroProductInfo)
        with connection.cursor() as cursor:
            # Use a parameterized query to prevent SQL injection
            placeholders = ",".join(["%s"] * len(symbols))
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE symbol IN ({placeholders})
                """,  # nosec B608
                symbols,
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["id"]: row for row in rows}
        return result_map

    @staticmethod
    def get_product_info_from_id(product_id: int) -> dict:
        """Get product information from the given product id. The information is retrieved from the DB."""
        return ProductInfoRepository.get_products_info_raw([product_id])[product_id]

    @staticmethod
    def get_product_info_from_name(name: str) -> dict:
        """Gets product information from the given product name. The information is retrieved from the DB.
        ### Parameters
            * productName
        ### Returns
            Product Info
        """
        connection = get_connection_for_model(DeGiroProductInfo)
        with connection.cursor() as cursor:
            # Use parameterized query to prevent SQL injection
            cursor.execute(
                """
                SELECT *
                FROM degiro_productinfo
                WHERE name = %s
                LIMIT 1
                """,
                [name],
            )
            return dictfetchone(cursor)

    @staticmethod
    def get_products_isin() -> list[str]:
        """Get product information. The information is retrieved from the DB.

        ### Returns
            list: list of product ISINs
        """
        connection = get_connection_for_model(DeGiroProductInfo)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT isin FROM degiro_productinfo
                """,
            )
            result = dictfetchall(cursor)

        isin_list = [row["isin"] for row in result]
        return list(set(isin_list))
