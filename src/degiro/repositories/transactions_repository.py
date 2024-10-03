from datetime import date

from django.db import connection
from django.forms import model_to_dict

from degiro.models import Transactions
from degiro.utils.db_utils import dictfetchall


class TransactionsRepository:
    @staticmethod
    def get_transactions_raw() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_last_movement() -> date | None:
        """Return the latest update from the DB.

        ### Returns:
            date: the latest update from the DB, None if there is no entry
        """
        try:
            entry = Transactions.objects.all().order_by("-date").first()
            if entry is not None:
                oldest_day = model_to_dict(entry)["date"]
                return oldest_day.date()
        except Exception:
            """Ignore. The Database doesn't contain anything"""

        return None
