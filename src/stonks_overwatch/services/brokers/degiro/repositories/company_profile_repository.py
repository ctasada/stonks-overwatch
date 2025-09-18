import json

from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroCompanyProfile
from stonks_overwatch.utils.database.db_utils import dictfetchall, get_connection_for_model


class CompanyProfileRepository:
    @staticmethod
    def get_company_profile_raw(isin: str) -> dict | None:
        connection = get_connection_for_model(DeGiroCompanyProfile)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_companyprofile
                WHERE isin = %s
                """,
                [isin],
            )
            result = dictfetchall(cursor)

        if result:
            return json.loads(result[0]["data"])
        return None
