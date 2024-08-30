"""Imports DeGiro Transaction information.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript transactions_import
"""

import json
from datetime import date, datetime, time, timedelta

from degiro_connector.trading.models.transaction import HistoryRequest
from django.forms import model_to_dict

from degiro.config.degiro_config import DegiroConfig
from degiro.models import Transactions
from degiro.utils.degiro import DeGiro
from scripts.commons import IMPORT_FOLDER, TIME_DATE_FORMAT, init


def get_import_from_date() -> date:
    """Return the latest update from the DB and increases to next day or defaults to configured date.

    ### Returns:
        date: the latest update from the DB and increases to next day or defaults to configured date.
    """
    degiro_config = DegiroConfig.default()
    try:
        entry = Transactions.objects.all().order_by("-date").first()
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


def get_transactions(from_date, json_file_path) -> None:
    """Import Transactions data from DeGiro. Uses the `get_transactions_history` method.

    ### Parameters
        * from_date : date
            - Starting date to import the data
        * json_file_path : str
            - Path to the Json file to store the transaction information
    ### Returns:
        None.
    """
    trading_api = DeGiro.get_client()

    request = HistoryRequest(from_date=from_date, to_date=date.today())

    # FETCH DATA
    transactions_history = trading_api.get_transactions_history(
        transaction_request=request,
        raw=True,
    )

    # Save the JSON to a file
    data_file = open(json_file_path, "w")
    data_file.write(json.dumps(transactions_history, indent=4))
    data_file.close()


def import_transactions(file_path) -> None:
    """Store the Transactions into the DB.

    ### Parameters
        * file_path : str
            - Path to the Json file that stores the transactions data
    ### Returns:
        None.
    """
    with open(file_path) as json_file:
        data = json.load(json_file)

    for row in data["data"]:
        try:
            Transactions.objects.update_or_create(
                id=row["id"],
                defaults={
                    "product_id": row["productId"],
                    "date": datetime.strptime(row["date"], TIME_DATE_FORMAT),
                    "buysell": row["buysell"],
                    "price": row["price"],
                    "quantity": row["quantity"],
                    "total": row["total"],
                    "order_type_id": row.get("orderTypeId", None),
                    "counter_party": row.get("counterParty", None),
                    "transfered": row["transfered"],
                    "fx_rate": row["fxRate"],
                    "nett_fx_rate": row["nettFxRate"],
                    "gross_fx_rate": row["grossFxRate"],
                    "auto_fx_fee_in_base_currency": row["autoFxFeeInBaseCurrency"],
                    "total_in_base_currency": row["totalInBaseCurrency"],
                    "fee_in_base_currency": row.get("feeInBaseCurrency", None),
                    "total_fees_in_base_currency": row["totalFeesInBaseCurrency"],
                    "total_plus_fee_in_base_currency": row["totalPlusFeeInBaseCurrency"],
                    "total_plus_all_fees_in_base_currency": row["totalPlusAllFeesInBaseCurrency"],
                    "transaction_type_id": row["transactionTypeId"],
                    "trading_venue": row.get("tradingVenue", None),
                    "executing_entity_id": row.get("executingEntityId", None),
                },
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)


def run():
    init()
    from_date = get_import_from_date()
    print(f"Importing DeGiro Transactions from {from_date}...")
    get_transactions(from_date, f"{IMPORT_FOLDER}/transactions.json")
    import_transactions(f"{IMPORT_FOLDER}/transactions.json")


if __name__ == "__main__":
    run()
