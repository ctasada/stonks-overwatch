"""Imports DeGiro Account information.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript account_import
"""

from degiro.config.degiro_config import DegiroConfig
from scripts.commons import IMPORT_FOLDER, TIME_DATE_FORMAT, init, save_to_json

import json
import pandas as pd

from datetime import date, datetime, time, timedelta
from django.forms import model_to_dict

from degiro.utils.degiro import DeGiro
from degiro.models import CashMovements

from degiro_connector.trading.models.account import OverviewRequest


def get_import_from_date() -> date:
    """
    Returns the latest update from the DB and increases to next day or defaults to configured date
    ### Returns:
        date: the latest update from the DB and increases to next day or defaults to configured date
    """
    degiro_config = DegiroConfig.default()
    try:
        entry = CashMovements.objects.all().order_by("-date").first()
        if entry is not None:
            oldest_day = model_to_dict(entry)["date"]
            oldest_day += timedelta(days=1)
            return datetime.combine(oldest_day, time.min)
    except Exception:
        print("Something went wrong, defaulting to oldest date")

    return date(
        year=degiro_config.start_date.year,
        month=degiro_config.start_date.month,
        day=degiro_config.start_date.day,
    )


def get_cash_movements(from_date: date, json_file_path: str) -> None:
    """
    Import Account data from DeGiro. Uses the `get_account_overview` method.
    ### Parameters
        * from_date : date
            - Starting date to import the data
        * json_file_path : str
            - Path to the Json file to store the account information
    ### Returns:
        None
    """
    trading_api = DeGiro.get_client()

    request = OverviewRequest(from_date=from_date, to_date=date.today())

    # FETCH DATA
    account_overview = trading_api.get_account_overview(
        overview_request=request,
        raw=True,
    )

    # Save the JSON to a file
    save_to_json(account_overview, json_file_path)


def transform_json(json_file_path: str, output_file_path: str) -> None:
    """
    Flattens the data from deGiro `get_account_overview` method for easier manipulation when inserting it into the DB.
    ### Parameters
        * json_file_path : str
            - Path to the Json file that stores the account information
        * output_file_path : str
            - Path to the Json file to store the flatten data
    ### Returns:
        None
    """
    with open(json_file_path) as json_file:
        data = json.load(json_file)

    if data["data"]:
        # Use pd.json_normalize to convert the JSON to a DataFrame
        df = pd.json_normalize(data["data"]["cashMovements"], sep="_")
        # Fix id values format after Pandas
        for col in ["productId", "id"]:
            df[col] = df[col].apply(
                lambda x: None if pd.isnull(x) else str(x).replace(".0", "")
            )

        # Set the index explicitly
        df.set_index("date", inplace=True)

        # Sort the DataFrame by the 'date' column
        df = df.sort_values(by="date")

        transformed_json = json.loads(df.reset_index().to_json(orient="records"))
    else:
        transformed_json = None

    # ## Save the JSON to a file
    save_to_json(transformed_json, output_file_path)


def _conv(i):
    return i or None


def import_cash_movements(file_path: str) -> None:
    """
    Stores the cash movements into the DB.
    ### Parameters
        * file_path : str
            - Path to the Json file that stores the flatten account information data
    ### Returns:
        None
    """
    with open(file_path) as json_file:
        data = json.load(json_file)

    if data:
        for row in data:
            try:
                CashMovements.objects.create(
                    date=datetime.strptime(row["date"], TIME_DATE_FORMAT),
                    valueDate=datetime.strptime(row["valueDate"], TIME_DATE_FORMAT),
                    description=row["description"],
                    productId=row.get("productId"),
                    currency=row["currency"],
                    type=row["type"],
                    change=_conv(row.get("change", None)),
                    balance_unsettledCash=row.get("balance_unsettledCash", None),
                    balance_flatexCash=row.get("balance_flatexCash", None),
                    balance_cashFund=row.get("balance_cashFund", None),
                    balance_total=row.get("balance_total", None),
                    exchangeRate=_conv(row.get("exchangeRate", None)),
                    orderId=row.get("orderId", None),
                )
            except Exception as error:
                print(f"Cannot import row: {row}")
                print("Exception: ", error)


def run():
    """
    Imports DeGiro Account information.
    """
    init()
    from_date = get_import_from_date()
    get_cash_movements(from_date, f"{IMPORT_FOLDER}/account.json")
    transform_json(
        f"{IMPORT_FOLDER}/account.json", f"{IMPORT_FOLDER}/account_transform.json"
    )
    import_cash_movements(f"{IMPORT_FOLDER}/account_transform.json")


if __name__ == "__main__":
    run()
