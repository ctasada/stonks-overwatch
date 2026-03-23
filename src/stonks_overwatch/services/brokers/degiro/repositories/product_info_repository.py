from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductInfo
from stonks_overwatch.utils.database.db_utils import snake_to_camel


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
        if not ids:
            return {}

        rows = [
            {snake_to_camel(key): value for key, value in row.items()}
            for row in DeGiroProductInfo.objects.filter(id__in=ids).values()
        ]

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
        if not symbols:
            return {}

        rows = [
            {snake_to_camel(key): value for key, value in row.items()}
            for row in DeGiroProductInfo.objects.filter(symbol__in=symbols).values()
        ]

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row["id"]: row for row in rows}
        return result_map

    @staticmethod
    def get_product_info_from_id(product_id: int) -> dict:
        """Get product information from the given product id. The information is retrieved from the DB.

        Returns an empty dict if the product is not found.
        """
        return ProductInfoRepository.get_products_info_raw([product_id]).get(product_id, {})

    @staticmethod
    def get_product_info_from_name(name: str) -> dict:
        """Gets product information from the given product name. The information is retrieved from the DB.
        ### Parameters
            * productName
        ### Returns
            Product Info
        """
        row = DeGiroProductInfo.objects.filter(name=name).values().first()
        if row is None:
            return None
        return {snake_to_camel(key): value for key, value in row.items()}

    @staticmethod
    def get_products_isin() -> list[str]:
        """Get product information. The information is retrieved from the DB.

        ### Returns
            list: list of product ISINs
        """
        return list(set(DeGiroProductInfo.objects.values_list("isin", flat=True)))
