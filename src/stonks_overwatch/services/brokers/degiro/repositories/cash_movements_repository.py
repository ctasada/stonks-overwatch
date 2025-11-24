from datetime import datetime

from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroCashMovements
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model


class CashMovementsRepository:
    @staticmethod
    def get_cash_movements_raw() -> list[dict]:
        connection = get_connection_for_model(DeGiroCashMovements)
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
        connection = get_connection_for_model(DeGiroCashMovements)
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
        connection = get_connection_for_model(DeGiroCashMovements)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, balance_total
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                  AND type IN ('CASH_TRANSACTION', 'FLATEX_CASH_SWEEP')
                  AND id IN (
                    SELECT MAX(id)
                    FROM degiro_cashmovements
                    WHERE currency = 'EUR'
                      AND type IN ('CASH_TRANSACTION', 'FLATEX_CASH_SWEEP')
                    GROUP BY DATE(date)
                )
                ORDER BY date
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_total_cash_deposits_raw() -> float:
        connection = get_connection_for_model(DeGiroCashMovements)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT SUM(change)
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                  AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting', 'flatex terugstorting')
                ORDER BY date, id
                """
            )
            return cursor.fetchone()[0]

    @staticmethod
    def get_total_cash(currency: str) -> float | None:
        connection = get_connection_for_model(DeGiroCashMovements)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance_total
                FROM degiro_cashmovements
                WHERE type = 'FLATEX_CASH_SWEEP'
                    AND currency = %s
                ORDER BY date DESC, id DESC
                LIMIT 1
                """,
                [currency],
            )

            result = dictfetchall(cursor)
            if result:
                balance_total = result[0].get("balanceTotal")
                return float(balance_total) if balance_total is not None else None

            return None

    @staticmethod
    def get_last_movement() -> datetime | None:
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
