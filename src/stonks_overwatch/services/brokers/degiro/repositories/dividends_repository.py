from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroAgendaDividend, DeGiroUpcomingPayments
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model


class DividendsRepository:
    @staticmethod
    def get_upcoming_payments() -> list[dict]:
        connection = get_connection_for_model(DeGiroUpcomingPayments)
        with connection.cursor() as cursor:
            # In case the date is the same, use the id to provide a consistent sorting
            cursor.execute(
                """
                SELECT *
                FROM degiro_upcomingpayments
                ORDER BY pay_date DESC, id DESC
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_forecasted_payments(isin: str) -> dict:
        connection = get_connection_for_model(DeGiroAgendaDividend)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_agendadividend
                WHERE isin = %s
                ORDER BY date_time DESC, event_id DESC
                """,
                [isin],
            )
            result = dictfetchall(cursor)
            return result[0] if result else None
