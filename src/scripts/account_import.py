# IMPORTATIONS
import json
import csv

from datetime import date, datetime

from degiro.utils.degiro import DeGiro
from degiro.models import CashMovements

from degiro_connector.trading.models.account import OverviewRequest

## Import Account data from DeGiro ##
def get_cash_movements(file_path):
    trading_api = DeGiro.get_client()

    # SETUP REQUEST
    from_date = date(
        year=2020,
        month=1,
        day=1,
    )

    request = OverviewRequest(
        from_date=from_date,
        to_date=date.today(),
    )

    # FETCH DATA
    account_overview = trading_api.get_account_overview(
        overview_request=request,
        raw=True,
    )

    ## Save the JSON to a file
    data_file = open(file_path, 'w')
    data_file.write(json.dumps(account_overview, indent = 4))
    data_file.close()

## ---------------------- ##

## Convert Data to CSV ##
def convert_json_to_csv(json_file_path, csv_file_path):
    with open(json_file_path) as json_file:
        data = json.load(json_file)

    cashMovements = data['data']['cashMovements']

    # now we will open a file for writing
    data_file = open(csv_file_path, 'w')
    
    # create the csv writer object
    csv_writer = csv.writer(data_file)

    # The JSON is not consistent, some entries contain different fields
    header = ['date', 'valueDate', 'description', 'currency', 'change', 'type']
    # Writing headers of CSV file
    csv_writer.writerow(header)

    for entry in cashMovements:
        row = []
        # Some values we don't want to import, so lets skip them
        # - CASH_FUND_TRANSACTION ?????
        # - PAYMENT is allways followed by a CASH_TRANSACTION
        # - FLATEX_CASH_SWEEP is detailing the sweep to the account, so this value is kind of duplicated
        if (entry['type'] in ['CASH_FUND_TRANSACTION', 'FLATEX_CASH_SWEEP', 'PAYMENT']):
            print(entry)
            continue

        # Writing data of CSV file
        for field in header:
            row.append(entry.get(field))
        
        csv_writer.writerow(row)

    data_file.close()

def import_cash_movements(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            CashMovements.objects.create(
                date=datetime.strptime(row['date'], '%Y-%m-%dT%H:%M:%S%z').date(),
                valueDate=datetime.strptime(row['valueDate'], '%Y-%m-%dT%H:%M:%S%z').date(),
                description=row['description'],
                currency=row['currency'],
                type=row['type'],
                change=row['change']
            )

def run():
    # get_cash_movements('account.json')
    convert_json_to_csv('account.json', 'account.csv')
    import_cash_movements('account.csv')

if __name__ == '__main__':
    run()