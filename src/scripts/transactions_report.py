import array
import json
import pandas as pd
from datetime import date, datetime, time, timedelta

from django.db.models import Sum
from django.db import connection
from django.forms import model_to_dict
from degiro.models import Transactions
from degiro.utils.db_utils import dictfetchall

def get_productIds() -> array:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT productId FROM degiro_transactions GROUP BY productId
            """
            )
        results = dictfetchall(cursor)
    
    productIds = [entry['productId'] for entry in results]
    
    print (productIds)
    return productIds

def get_value_growth() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT date, productId, buysell, quantity, price, total FROM degiro_transactions
            """
            )
        results = dictfetchall(cursor)
    
    product_growth = {}
    for entry in results:
        key = entry['productId']
        product = product_growth.get(key, {})
        carry_total = product.get('carry_total', 0)

        stock_date = entry['date'].strftime('%Y-%m-%d')
        carry_total += entry['quantity']
        
        product['carry_total'] = carry_total
        product[stock_date] = carry_total
        product_growth[key] = product
    
    # We need to use the productIds to get the daily quote for each product

    # With everything now we need to calculate the daily aggregate

    print (print(json.dumps(product_growth, indent = 4)))

def run():
    get_productIds()
    get_value_growth()

if __name__ == '__main__':
    run()