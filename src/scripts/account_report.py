import pandas as pd
from datetime import date, datetime, time, timedelta

from django.db.models import Sum
from django.db import connection
from django.forms import model_to_dict
from degiro.models import CashMovements

def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def calculate_cash_account():
    # FIXME: the total value seems to be 24 cents larger :/
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT SUM(change) 
            FROM degiro_cashmovements 
            WHERE currency = 'EUR' 
                AND change IS NOT NULL 
                AND type IN ('TRANSACTION', 'CASH_TRANSACTION', 'CASH_FUND_TRANSACTION', 'CASH_FUND_NAV_CHANGE')
            """
            )
        total = cursor.fetchone()
    
    print (f"Calculated Cash Account = {total[0]}")

def calculate_cash_contributions():
    # FIXME: DeGiro doesn't a consistent description or type. Missing the new value for 'Refund'
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT date, description, change 
            FROM degiro_cashmovements 
            WHERE currency = 'EUR' 
                AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
            """
            )
        cashContributions = dictfetchall(cursor)
    
    df = pd.DataFrame.from_dict(cashContributions)
    total = df['change'].sum()

    print("Cash Contributions")
    print(df)
    print (f"Calculated Cash Contributions = {total}")

def run():
    calculate_cash_account()
    calculate_cash_contributions()
    # TODO: Calculate Dividends

if __name__ == '__main__':
    run()