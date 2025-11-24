import json

from stonks_overwatch.services.brokers.bitvavo.repositories.models import BitvavoProductQuotation
from stonks_overwatch.utils.database.db_utils import dictfetchone, get_connection_for_model


class ProductQuotationsRepository:
    @staticmethod
    def get_product_quotations(symbol: str) -> dict | None:
        """Gets the quotations from the specified product_id from the DB.

        ### Returns
            List of quotations, or None if the product is not found
        """
        connection = get_connection_for_model(BitvavoProductQuotation)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM bitvavo_productquotation WHERE symbol = %s
                """,
                [symbol],
            )
            results = dictfetchone(cursor)

        if results:
            return json.loads(results["quotations"])

        return None

    @staticmethod
    def get_product_price(symbol: str) -> float:
        """Gets the last quotation from the specified product_id from the DB.

        ### Returns
            Last quotation, or 0.0 if the product is not found
        """
        quotations = ProductQuotationsRepository.get_product_quotations(symbol)
        if quotations:
            last_quotation = list(quotations.keys())[-1]

            return quotations[last_quotation]

        return 0.0
