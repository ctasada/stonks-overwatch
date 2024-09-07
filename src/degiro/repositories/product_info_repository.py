from django.db import connection

from degiro.utils.db_utils import dictfetchall, dictfetchone


class ProductInfoRepository:
    def get_products_info_raw(self, ids) -> dict:
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

    def get_product_info_from_id(self, product_id: int) -> dict:
        """Get product information from the given product id. The information is retrieved from the DB."""
        return self.get_products_info_raw([product_id])[product_id]

    def get_product_info_from_name(self, name: str) -> dict:
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
