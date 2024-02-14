import json
from datetime import datetime, timedelta

from django.db import connection
from degiro.utils.db_utils import dictfetchall

from degiro.utils.degiro import DeGiro
from scripts.commons import DATE_FORMAT, IMPORT_FOLDER, save_to_json
from scripts.products_info_import import calculate_interval, get_productInfo, import_products_quotation

def get_product_quotations(productId: int) -> dict:
    """
    Gets the list of product ids from the DB.

    ### Returns
        list: list of product ids
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT quotations FROM degiro_productquotation WHERE id = %s
            """,
            [productId]
            )
        # FIXME: Avoid this manual conversion
        results = dictfetchall(cursor)[0]['quotations']
    
    return json.loads(results)

def _calculate_position_growth(entry: dict) -> dict:
    print(f"Processing {entry['product']['name']}")
    
    product_history_dates = list(entry['history'].keys())
    
    start_date = datetime.strptime(product_history_dates[0], DATE_FORMAT).date()
    if product_history_dates[-1] == 0:
        final_date = datetime.strptime(product_history_dates[-1], DATE_FORMAT).date()
    else:
        final_date = datetime.today().date()

    # difference between current and previous date
    delta = timedelta(days=1)
    # store the dates between two dates in a list
    dates = []
    while start_date <= final_date:
        # add current date to list by converting  it to iso format
        dates.append(start_date.strftime(DATE_FORMAT))
        # increment start date by timedelta
        start_date += delta

    position_value = dict()
    for date in entry['history']:
        index = dates.index(date)
        for d in dates[index:]:
            position_value[d] = entry['history'][date]

    aggregate = dict()
    for date in entry['quotation']['quotes']:
        aggregate[date] = position_value[date] * entry['quotation']['quotes'][date]

    return aggregate

def _get_usd_conversion() -> float:
    """
    Gets the USD/EUR relation.

    The value is retrieved from the DeGiro `get_products_info` method.

    ### Returns
        fx: The USD-EUR conversion rate
    """
    trading_api = DeGiro.get_client()
    usd_info = trading_api.get_products_info(
        product_list=[705366], # 705366 is the product id for the USD/EUR
        raw=True,
    )

    return usd_info['data']['705366']['closePrice']

def calculate_growth(json_file_path: str, dst_json_file: str) -> None:
    with open(json_file_path) as json_file:
        data = json.load(json_file)

    fx_rate = _get_usd_conversion()
    # FIXME: Maybe Pandas/Polar provides a better way
    # FIXME: We need to convert USD/EUR, here we ignore the currency
    # FIXME: Result seems that needs to be divided by TODAY's USD/EUR exchange rate.
    aggregate = dict()
    for key in data:
        entry = data[key]
        position_value_growth = _calculate_position_growth(entry)
        convert_fx = entry['product']['currency'] == 'USD'
        for date in position_value_growth:
            aggregate_value = aggregate.get(date, 0)
            if fx_rate:
                aggregate_value += position_value_growth[date] / fx_rate
            else:
                aggregate_value += position_value_growth[date]
            aggregate[date] = aggregate_value

    save_to_json(aggregate, dst_json_file)


def create_products_quotation(json_file_path) -> None:
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

        stock_date = entry['date'].strftime(DATE_FORMAT)
        carry_total += entry['quantity']
        
        product['carry_total'] = carry_total
        if 'history' not in product:
            product['history'] = {}    
        product['history'][stock_date] = carry_total
        product_growth[key] = product
    
    # Cleanup 'carry_total' from result
    for key in product_growth.keys():
        del product_growth[key]['carry_total']

    delete_keys = []
    for key in product_growth.keys():
        product = get_productInfo(key)
        
        # If the product is NOT tradable, we shouldn't consider it for Growth
        if product['tradable'] == False:
            delete_keys.append(key)
            continue
        
        product_growth[key]['product'] = {}
        product_growth[key]['product']['name'] = product['name']
        product_growth[key]['product']['isin'] = product['isin']
        product_growth[key]['product']['symbol'] = product['symbol']
        product_growth[key]['product']['currency'] = product['currency']
        product_growth[key]['product']['vwdId'] = product['vwdId']
        product_growth[key]['product']['vwdIdSecondary'] = product['vwdIdSecondary']

        # Calculate Quotation Range
        product_growth[key]['quotation'] = {}
        product_history_dates = list(product_growth[key]['history'].keys())
        start_date = product_history_dates[0]
        final_date = datetime.today().strftime(DATE_FORMAT)
        tmp_last = product_history_dates[-1]
        if product_growth[key]['history'][tmp_last] == 0:
            final_date = tmp_last
        
        product_growth[key]['quotation']['from_date'] = start_date
        product_growth[key]['quotation']['to_date'] = final_date
        # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
        product_growth[key]['quotation']['interval'] = calculate_interval(start_date)

    # Delete the non-tradable products
    for key in delete_keys:
        del product_growth[key]

    # We need to use the productIds to get the daily quote for each product
    for key in product_growth.keys():
        if product_growth[key]['product'].get('vwdIdSecondary') != None:
            issueId = product_growth[key]['product'].get('vwdIdSecondary') 
        else:
            issueId = product_growth[key]['product'].get('vwdId')
        
        interval = product_growth[key]['quotation']['interval']
        quotes_dict = get_product_quotations(key)

        product_growth[key]['quotation']['quotes'] = quotes_dict

    save_to_json(product_growth, json_file_path)

def run():
    create_products_quotation(f"{IMPORT_FOLDER}/product_quotations.json")
    calculate_growth(f"{IMPORT_FOLDER}/product_quotations.json", f"{IMPORT_FOLDER}/aggregate_value.json")

if __name__ == '__main__':
    run()