import json
import csv
import os
import pandas as pd

from datetime import date, datetime, time, timedelta
from django.forms import model_to_dict

from degiro.utils.degiro import DeGiro
from degiro.models import Transactions

from degiro_connector.trading.models.transaction import HistoryRequest

import_folder = './import'

def init():
    if not os.path.exists(import_folder):
        os.makedirs(import_folder)

## Obtains the latest update from the DB and increases to next day or defaults to January 2020
def get_import_from_date() -> date:
    try:
        entry = Transactions.objects.all().order_by('date').first()
        if entry is not None:
            oldest_day = model_to_dict( entry )['date']
            oldest_day += timedelta(days=1)
            return datetime.combine(oldest_day, time.min)
    except:
        print("Something went wrong, defaulting to oldest date")

    return date(year=2020, month=1, day=1)

## Import Account data from DeGiro ##
def get_transactions(from_date, json_file_path) -> None:
    trading_api = DeGiro.get_client()

    request = HistoryRequest(from_date=from_date, to_date=date.today())

    # FETCH DATA
    transactions_history = trading_api.get_transactions_history(
        transaction_request=request,
        raw=True,
    )

    ## Save the JSON to a file
    data_file = open(json_file_path, 'w')
    data_file.write(json.dumps(transactions_history, indent = 4))
    data_file.close()

def import_transactions(file_path) -> None:
    with open(file_path) as json_file:
        data = json.load(json_file)

    conv = lambda i : i or None
    for row in data['data']:
        try :
            Transactions.objects.create(
                id=row['id'],
                productId=row['productId'],
                date=datetime.strptime(row['date'], '%Y-%m-%dT%H:%M:%S%z'),
                buysell=row['buysell'],
                price=row['price'],
                quantity=row['quantity'],
                total=row['total'],
                orderTypeId=row.get('orderTypeId', None),
                counterParty=row.get('counterParty', None),
                transfered=row['transfered'],
                fxRate=row['fxRate'],
                nettFxRate=row['nettFxRate'],
                grossFxRate=row['grossFxRate'],
                autoFxFeeInBaseCurrency=row['autoFxFeeInBaseCurrency'],
                totalInBaseCurrency=row['totalInBaseCurrency'],
                feeInBaseCurrency=row.get('feeInBaseCurrency', None),
                totalFeesInBaseCurrency=row['totalFeesInBaseCurrency'],
                totalPlusFeeInBaseCurrency=row['totalPlusFeeInBaseCurrency'],
                totalPlusAllFeesInBaseCurrency=row['totalPlusAllFeesInBaseCurrency'],
                transactionTypeId=row['transactionTypeId'],
                tradingVenue=row.get('tradingVenue', None),
                executingEntityId=row.get('executingEntityId', None),
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)

def run():
    init()
    from_date = get_import_from_date()
    # get_transactions(from_date, f"{import_folder}/transactions.json")
    import_transactions(f"{import_folder}/transactions.json")

if __name__ == '__main__':
    run()