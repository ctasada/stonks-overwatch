import json
from datetime import datetime

from django.db import connection

from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductQuotation
from stonks_overwatch.utils.database.db_utils import dictfetchone

class ProductQuotationsRepository:
    @staticmethod
    def get_product_quotations(product_id: int) -> dict | None:
        """Gets the quotations from the specified product_id from the DB.

        ### Returns
            List of quotations, or None if the product is not found
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [product_id],
            )
            results = dictfetchone(cursor)

        if results:
            return json.loads(results["quotations"])

        return None

    @staticmethod
    def get_product_price(product_id: int) -> float:
        """Gets the last quotation from the specified product_id from the DB.

        ### Returns
            Last quotation, or 0.0 if the product is not found
        """
        quotations = ProductQuotationsRepository.get_product_quotations(product_id)
        if quotations:
            last_quotation = list(quotations.keys())[-1]

            return quotations[last_quotation]

        return 0.0

    @staticmethod
    def get_last_update() -> datetime|None:
        """Return the latest update from the DB.

        ### Returns:
            date: the latest update from the DB, None if there is no entry
        """
        try:
            entry = DeGiroProductQuotation.objects.all().order_by("-last_import").first()
            if entry is not None:
                return entry.last_import
        except Exception:
            """Ignore. The Database doesn't contain anything"""

        return None
