from datetime import date

from django.db import connection
from django.forms import model_to_dict

from degiro.models import Transactions
from degiro.utils.db_utils import dictfetchall


class TransactionsRepository:
    def get_transactions_raw(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)

    def get_last_movement(self) -> date:
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
