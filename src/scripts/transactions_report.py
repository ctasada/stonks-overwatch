import json
from datetime import date, datetime, timedelta

from django.db import connection
from degiro.utils.db_utils import dictfetchall

from degiro.utils.degiro import DeGiro
from scripts.commons import DATE_FORMAT, IMPORT_FOLDER, save_to_json
from scripts.products_info_import import import_products_quotation

def get_productIds() -> list:
    """
    Gets the list of product ids from the DB.

    ### Returns
        list: list of product ids
    """
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

def _calculate_growth(json_file_path) -> None:
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

    save_to_json(aggregate, f"{IMPORT_FOLDER}/aggregate_value.json")

def run():
    get_productIds()
    # FIXME: Replace by a Query once we have the data in the DB
    import_products_quotation()
    _calculate_growth(f"{IMPORT_FOLDER}/transform.json")

if __name__ == '__main__':
    run()