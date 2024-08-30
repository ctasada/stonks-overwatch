import json

from django.db import connection

from degiro.utils.db_utils import dictfetchall


class CompanyProfileRepository:
    def get_company_profile_raw(self, isin: str) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_companyprofile
                WHERE isin = %s
                """,
                [isin],
            )
            rows = dictfetchall(cursor)

        return json.loads(rows[0]["data"])
