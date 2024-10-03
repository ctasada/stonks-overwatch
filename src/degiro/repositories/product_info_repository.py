from django.db import connection

from degiro.utils.db_utils import dictfetchall, dictfetchone


class ProductInfoRepository:
    @staticmethod
    def get_products_info_raw(ids) -> dict:
        """Gets product information from the given product id. The information is retrieved from the DB.
        ### Parameters
            * productIds: list of ints
                - The product ids to query
        ### Returns
            list: list of product infos
        """
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE id IN ({", ".join(map(str, ids))})
                """
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
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE name = '{name}'
                LIMIT 1
                """
            )
            return dictfetchone(cursor)

    @staticmethod
    def get_products_isin() -> list[str]:
        """Get product information. The information is retrieved from the DB.

        ### Returns
            list: list of product ISINs
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT isin FROM degiro_productinfo
                """,
            )
            result = dictfetchall(cursor)

        isin_list = [row["isin"] for row in result]
        return list(set(isin_list))
