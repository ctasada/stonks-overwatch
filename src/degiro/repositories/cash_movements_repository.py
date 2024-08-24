
from django.db import connection

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

    def get_cash_deposits_raw(self) -> dict:
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
