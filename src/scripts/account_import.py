import json
import os
import pandas as pd

from datetime import date, datetime, time, timedelta
from django.forms import model_to_dict

from degiro.utils.degiro import DeGiro
from degiro.models import CashMovements

from degiro_connector.trading.models.account import OverviewRequest

import_folder = './import'

def init():
    if not os.path.exists(import_folder):
        os.makedirs(import_folder)

## Obtains the latest update from the DB and increases to next day or defaults to January 2020
def get_import_from_date() -> date:
    try:
        entry = CashMovements.objects.all().order_by('date').first()
        if entry is not None:
            oldest_day = model_to_dict( entry )['date']
            oldest_day += timedelta(days=1)
            return datetime.combine(oldest_day, time.min)
    except:
        print("Something went wrong, defaulting to oldest date")

    return date(year=2020, month=1, day=1)

## Import Account data from DeGiro ##
def get_cash_movements(from_date, json_file_path) -> None:
    trading_api = DeGiro.get_client()

    request = OverviewRequest(from_date=from_date, to_date=date.today())

    # FETCH DATA
    account_overview = trading_api.get_account_overview(
        overview_request=request,
        raw=True,
    )

    ## Save the JSON to a file
    data_file = open(json_file_path, 'w')
    data_file.write(json.dumps(account_overview, indent = 4))
    data_file.close()

## ---------------------- ##

def transform_json(json_file_path, output_file_path) -> None:
    with open(json_file_path) as json_file:
        data = json.load(json_file)

    # Use pd.json_normalize to convert the JSON to a DataFrame
    df = pd.json_normalize(data['data']['cashMovements'], sep='_')
    # Fix id values format after Pandas
    for col in ['productId', 'id']:
        df[col] = df[col].apply(lambda x: None if pd.isnull(x) else str(x).replace('.0', ''))

    # Set the index explicitly
    df.set_index('date', inplace=True)

    # Sort the DataFrame by the 'date' column
    df = df.sort_values(by='date')

    transformed_json = json.loads(df.reset_index().to_json(orient='records'))

    # ## Save the JSON to a file
    data_file = open(output_file_path, 'w')
    data_file.write(json.dumps(transformed_json, indent = 4))
    data_file.close()

def import_cash_movements(file_path) -> None:
    with open(file_path) as json_file:
        data = json.load(json_file)

    conv = lambda i : i or None
    for row in data:
        try :
            CashMovements.objects.create(
                date=datetime.strptime(row['date'], '%Y-%m-%dT%H:%M:%S%z'),
                valueDate=datetime.strptime(row['valueDate'], '%Y-%m-%dT%H:%M:%S%z'),
                description=row['description'],
                productId=row.get('productId'),
                currency=row['currency'],
                type=row['type'],
                change=conv(row.get('change', None)),
                balance_unsettledCash=row.get('balance_unsettledCash', None),
                balance_flatexCash=row.get('balance_flatexCash', None),
                balance_cashFund=row.get('balance_cashFund', None),
                balance_total=row.get('balance_total', None),
                exchangeRate=conv(row.get('exchangeRate', None)),
                orderId=row.get('orderId', None)
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)

def run():
    from_date = get_import_from_date()
    get_cash_movements(from_date, f"{import_folder}/account.json")
    transform_json(f"{import_folder}/account.json", f"{import_folder}/account_transform.json")
    import_cash_movements(f"{import_folder}/account_transform.json")

if __name__ == '__main__':
    run()