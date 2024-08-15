"""Imports DeGiro Transaction information.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript transactions_import
"""
import json

from datetime import date, datetime, time, timedelta
from django.forms import model_to_dict

from degiro.utils.degiro import DeGiro
from degiro.models import Transactions

from degiro_connector.trading.models.transaction import HistoryRequest

from scripts.commons import IMPORT_FOLDER, TIME_DATE_FORMAT, init


def get_import_from_date() -> date:
    """
    Returns the latest update from the DB and increases to next day or defaults to January 2020
    ### Returns:
        date: the latest update from the DB and increases to next day or defaults to January 2020
    """
    try:
        entry = Transactions.objects.all().order_by('-date').first()
        if entry is not None:
            oldest_day = model_to_dict(entry)['date']
            oldest_day += timedelta(days=1)
            return datetime.combine(oldest_day, time.min)
    except Exception:
        print("Something went wrong, defaulting to oldest date")

    return date(year=2020, month=1, day=1)


def get_transactions(from_date, json_file_path) -> None:
    """
    Import Transactions data from DeGiro. Uses the `get_transactions_history` method.
    ### Parameters
        * from_date : date
            - Starting date to import the data
        * json_file_path : str
            - Path to the Json file to store the transaction information
    ### Returns:
        None
    """
    trading_api = DeGiro.get_client()

    request = HistoryRequest(from_date=from_date, to_date=date.today())

    # FETCH DATA
    transactions_history = trading_api.get_transactions_history(
        transaction_request=request,
        raw=True,
    )

    # Save the JSON to a file
    data_file = open(json_file_path, 'w')
    data_file.write(json.dumps(transactions_history, indent=4))
    data_file.close()


def import_transactions(file_path) -> None:
    """
    Stores the Transactions into the DB.
    ### Parameters
        * file_path : str
            - Path to the Json file that stores the transactions data
    ### Returns:
        None
    """
    with open(file_path) as json_file:
        data = json.load(json_file)

    for row in data['data']:
        try :
            Transactions.objects.update_or_create(
                id=row['id'],
                defaults={
                    'productId': row['productId'],
                    'date': datetime.strptime(row['date'], TIME_DATE_FORMAT),
                    'buysell': row['buysell'],
                    'price': row['price'],
                    'quantity': row['quantity'],
                    'total': row['total'],
                    'orderTypeId': row.get('orderTypeId', None),
                    'counterParty': row.get('counterParty', None),
                    'transfered': row['transfered'],
                    'fxRate': row['fxRate'],
                    'nettFxRate': row['nettFxRate'],
                    'grossFxRate': row['grossFxRate'],
                    'autoFxFeeInBaseCurrency': row['autoFxFeeInBaseCurrency'],
                    'totalInBaseCurrency': row['totalInBaseCurrency'],
                    'feeInBaseCurrency': row.get('feeInBaseCurrency', None),
                    'totalFeesInBaseCurrency': row['totalFeesInBaseCurrency'],
                    'totalPlusFeeInBaseCurrency': row['totalPlusFeeInBaseCurrency'],
                    'totalPlusAllFeesInBaseCurrency': row['totalPlusAllFeesInBaseCurrency'],
                    'transactionTypeId': row['transactionTypeId'],
                    'tradingVenue': row.get('tradingVenue', None),
                    'executingEntityId': row.get('executingEntityId', None),
                }
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)


def run():
    init()
    from_date = get_import_from_date()
    get_transactions(from_date, f"{IMPORT_FOLDER}/transactions.json")
    import_transactions(f"{IMPORT_FOLDER}/transactions.json")


if __name__ == '__main__':
    run()
