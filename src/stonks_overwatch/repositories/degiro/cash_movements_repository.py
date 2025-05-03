from datetime import datetime

from django.db import connection

from stonks_overwatch.repositories.degiro.models import DeGiroCashMovements
from stonks_overwatch.utils.db_utils import dictfetchall

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
        # FIXME: DeGiro doesn't have a consistent description or type.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting', 'flatex terugstorting')
                ORDER BY date
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
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting', 'flatex terugstorting')
                """
            )
            return cursor.fetchone()[0]

    @staticmethod
    def get_total_cash(currency: str) -> float:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance_total
                FROM degiro_cashmovements
                WHERE type = 'FLATEX_CASH_SWEEP'
                    AND currency = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                [currency],
            )
            balance_total = dictfetchall(cursor)[0]["balanceTotal"]
            return float(balance_total)

    @staticmethod
    def get_last_movement() -> datetime|None:
        """Return the latest update from the DB.

        ### Returns:
            date: the latest update from the DB, None if there is no entry
        """
        try:
            entry = DeGiroCashMovements.objects.all().order_by("-date").first()
            if entry is not None:
                return entry.date
        except Exception:
            """Ignore. The Database doesn't contain anything"""

        return None
