from datetime import date

from django.db import connection
from django.forms import model_to_dict

from degiro.models import CashMovements
from degiro.utils.db_utils import dictfetchall


class CashMovementsRepository:
    def get_cash_movements_raw(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_cashmovements
                ORDER BY date DESC
                """
            )
            return dictfetchall(cursor)

    def get_cash_deposits_raw(self) -> list:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
            )
            return dictfetchall(cursor)

    def get_total_cash_deposits_raw(self) -> float:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT SUM(change)
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
            )
            return cursor.fetchone()[0]

    def get_total_cash(self) -> float:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance_total
                FROM degiro_cashmovements
                ORDER BY id DESC
                LIMIT 1
                """
            )
            balance_total = dictfetchall(cursor)[0]["balanceTotal"]
            return float(balance_total)

    def get_last_movement(self) -> date:
        """Return the latest update from the DB.

        ### Returns:
            date: the latest update from the DB, None if there is no entry
        """
        try:
            entry = CashMovements.objects.all().order_by("-date").first()
            if entry is not None:
                oldest_day = model_to_dict(entry)["date"]
                return oldest_day.date()
        except Exception:
            """Ignore. The Database doesn't contain anything"""

        return None
