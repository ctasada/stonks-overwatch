from datetime import date

from django.db import connection
from django.forms import model_to_dict

from degiro.models import CashMovements
from degiro.utils.db_utils import dictfetchall


class CashMovementsRepository:
    @staticmethod
    def get_cash_movements_raw() -> list[dict]:
        with connection.cursor() as cursor:
            # In case the date is the same, use the id to provide a consistent sorting
            cursor.execute(
                """
                SELECT *
                FROM degiro_cashmovements
                ORDER BY date DESC, id DESC
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_cash_deposits_raw() -> list[dict]:
        # FIXME: DeGiro doesn't a consistent description or type. Missing the new value for 'Refund'
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

    @staticmethod
    def get_cash_balance_by_date() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, balance_total
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND type = 'CASH_TRANSACTION'
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_total_cash_deposits_raw() -> float:
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

    @staticmethod
    def get_total_cash() -> float:
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

    @staticmethod
    def get_last_movement() -> date|None:
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
