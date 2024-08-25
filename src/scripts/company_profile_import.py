"""Imports DeGiro Company Profiles.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript company_profile_import
"""

import json

from django.db import connection

from degiro.utils.db_utils import dictfetchall
from degiro.utils.degiro import DeGiro
from degiro.models import CompanyProfile

from scripts.commons import IMPORT_FOLDER, init


def get_company_profiles(json_file_path) -> None:
    """
    Import Company Profiles data from DeGiro. Uses the `get_transactions_history` method.
    ### Parameters
        * json_file_path : str
            - Path to the Json file to store the company profiles information
    ### Returns:
        None
    """
    products_isin = __get_productsISIN()

    company_profiles = {}

    for isin in products_isin:
        company_profile = DeGiro.get_client().get_company_profile(
            product_isin=isin,
            raw=True,
        )
        company_profiles[isin] = company_profile

    # Save the JSON to a file
    data_file = open(json_file_path, "w")
    data_file.write(json.dumps(company_profiles, indent=4))
    data_file.close()


def __get_productsISIN() -> dict:
    """
    Gets product information. The information is retrieved from the DB.
    ### Returns
        list: list of product ISINs
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT isin FROM degiro_productinfo
            """,
        )
        result = dictfetchall(cursor)

    isin_list = [row['isin'] for row in result]
    return list(set(isin_list))


def import_company_profiles(file_path) -> None:
    """
    Stores the Company Profiles into the DB.
    ### Parameters
        * file_path : str
            - Path to the Json file that stores the company profiles
    ### Returns:
        None
    """
    with open(file_path) as json_file:
        data = json.load(json_file)

    for key in data:
        try:
            CompanyProfile.objects.update_or_create(
                isin=key,
                data=data[key],
            )
        except Exception as error:
            print(f"Cannot import ISIN: {key}")
            print("Exception: ", error)


def run():
    init()
    print("Importing DeGiro Company Profiles...")
    get_company_profiles(f"{IMPORT_FOLDER}/company_profiles.json")
    import_company_profiles(f"{IMPORT_FOLDER}/company_profiles.json")


if __name__ == "__main__":
    run()
