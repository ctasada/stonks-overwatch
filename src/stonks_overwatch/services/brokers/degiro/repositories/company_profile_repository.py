import json

from django.db import connection

from stonks_overwatch.utils.database.db_utils import dictfetchall


class CompanyProfileRepository:
    @staticmethod
    def get_company_profile_raw(isin: str) -> dict | None:
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
