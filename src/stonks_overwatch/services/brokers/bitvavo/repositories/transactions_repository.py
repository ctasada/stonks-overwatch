from stonks_overwatch.services.brokers.bitvavo.repositories.models import BitvavoTransactions
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model


class TransactionsRepository:
    @staticmethod
    def get_transactions_raw() -> list[dict]:
        connection = get_connection_for_model(BitvavoTransactions)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_transactions
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_deposits_history_raw() -> list[dict]:
        connection = get_connection_for_model(BitvavoTransactions)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_transactions
                WHERE type = 'deposit'
                """
            )
            return dictfetchall(cursor)
