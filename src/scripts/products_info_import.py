"""Imports Product Information from DeGiro.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript products_info_import
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import polars as pl

from django.db import connection

from scripts.commons import DATE_FORMAT, IMPORT_FOLDER, init, save_to_json

from degiro.utils.degiro import DeGiro
from degiro.models import ProductInfo, ProductQuotation
from degiro.utils.db_utils import dictfetchall
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.quotecast.models.chart import ChartRequest, Interval

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
    
    return productIds

def get_products_info(product_ids:list, json_file_path:str) -> None:
    """
    Retrieves from DeGiro the product information of the indicated products.
    ### Parameters
        * product_ids: list
            - List with the product_ids to import
        * json_file_path : str
            - Path to the Json file to store the account information
    ### Returns
        None
    """
    trading_api = DeGiro.get_client()

    products_info = trading_api.get_products_info(
        product_list=list(set(product_ids)),
        raw=True,
    )

    ## Save the JSON to a file
    save_to_json(products_info, json_file_path)

def import_products_info(file_path:str) -> None:
    """
    Stores the products information into the DB.
    ### Parameters
        * file_path : str
            - Path to the Json file that stores the product information data
    ### Returns:
        None
    """
    with open(file_path) as json_file:
        data = json.load(json_file)

    conv = lambda i : i or None
    for key in data['data']:
        row = data['data'][key]
        try :
            ProductInfo.objects.update_or_create(
                id=int(row['id']),
                name=row['name'],
                isin=row['isin'],
                symbol=row['symbol'],
                contractSize=row['contractSize'],
                productType=row['productType'],
                productTypeId=row['productTypeId'],
                tradable=row['tradable'],
                category=row['category'],
                currency=row['currency'],
                active=row['active'],
                exchangeId=row['exchangeId'],
                onlyEodPrices=row['onlyEodPrices'],
                isShortable=row['isShortable'],
                feedQuality=row.get('feedQuality'),
                orderBookDepth=row.get('orderBookDepth'),
                vwdIdentifierType=row.get('vwdIdentifierType'),
                vwdId=row.get('vwdId'),
                qualitySwitchable=row.get('qualitySwitchable'),
                qualitySwitchFree=row.get('qualitySwitchFree'),
                vwdModuleId=row.get('vwdModuleId'),
                feedQualitySecondary=row.get('feedQualitySecondary'),
                orderBookDepthSecondary=row.get('orderBookDepthSecondary'),
                vwdIdentifierTypeSecondary=row.get('vwdIdentifierTypeSecondary'),
                vwdIdSecondary=row.get('vwdIdSecondary'),
                qualitySwitchableSecondary=row.get('qualitySwitchableSecondary'),
                qualitySwitchFreeSecondary=row.get('qualitySwitchFreeSecondary'),
                vwdModuleIdSecondary=row.get('vwdModuleIdSecondary')
            )
        except Exception as error:
            print(f"Cannot import row: {row}")
            print("Exception: ", error)

def get_productInfo(productId: int) -> dict:
    """
    Gets product information from the given product id. The information is retrieved from the DB.
    ### Parameters
        * productId: int
            - The product id to query
    ### Returns
        list: list of product ids
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM degiro_productinfo WHERE id = %s
            """,
            [productId]
            )
        result = dictfetchall(cursor)[0]
    
    return result


def calculate_interval(date_from) -> Interval:
    """
    Calculates the interval between the provided date and today
    ### Parameters
        date_from: date from to calculate the interval
    ### Returns
        Interval: Interval that representes the range from date_from to today
    """
    # Convert String to date object
    d1 = datetime.strptime(date_from, DATE_FORMAT)
    today = datetime.today()
    # difference between dates in timedelta
    delta = (today - d1).days

    interval = None
    match delta:
        case diff if diff in range(1, 7):
            interval = Interval.P1W
        case diff if diff in range(7, 30):
            interval = Interval.P1M
        case diff if diff in range(30, 90):
            interval = Interval.P3M
        case diff if diff in range(90, 180):
            interval = Interval.P6M
        case diff if diff in range(180, 365):
            interval = Interval.P1Y
        case diff if diff in range(365, 3*365):
            interval = Interval.P3Y
        case diff if diff in range(3*365, 5*365):
            interval = Interval.P5Y
        case diff if diff in range(5*365, 10*365):
            interval = Interval.P10Y

    return interval

def convert_interval_to_days(interval: Interval) -> int:
    """
    Converts and interval into the number of days
    ### Parameters
        interval: Interval
    ### Returns
        int: Number of days in the interval
    """
    match interval:
        case Interval.P1W:
            return 7
        case Interval.P1M:
            return 30
        case Interval.P3M:
            return 90
        case Interval.P6M:
            return 180
        case Interval.P1Y:
            return 365
        case Interval.P3Y:
            return 3 * 365
        case Interval.P5Y:
            return 5 * 365
        case Interval.P10Y:
            return 10 * 365

def _calculate_dates(interval) -> list:
    # Convert values to dates
    today = datetime.today().date()
    days = convert_interval_to_days(interval)
    start_date = today - relativedelta(days=days)
    result = []
    for i in range(1, days):
        day = start_date + relativedelta(days=i)
        result.append(day)
    
    return result

def get_product_quotation(issueid, period: Interval) -> list:
    """
    Get the list of quotations for the provided product for the indicated Interval.

    ### Parameters
        * issueid
            - ID representing the product. Should be 'vwdIdSecondary' or 'vwdId'
        * interval:
            - Time period from today to the past to retrieve the quotations
    ### Returns
        list: List with the quotations
    """
    # Retrieve user_token
    trading_api = DeGiro.get_client()
    client_details_table = trading_api.get_client_details()
    # int_account = client_details_table['data']['intAccount']
    user_token = client_details_table['data']['id']

    chart_fetcher = ChartFetcher(user_token=user_token)
    chart_request = ChartRequest(
        culture="nl-NL",
        period=period,
        requestid="1",
        resolution=Interval.P1D,
        series=[
            f"issueid:{issueid}",
            f"price:issueid:{issueid}",
        ],
        tz="Europe/Amsterdam",
    )
    chart = chart_fetcher.get_chart(
        chart_request=chart_request,
        raw=False,
    )

    quotes = None
    for series in chart.series:
        if (series.type == 'time'):
            # 'column_0' is the position, and 'column_1' is the value.
            data_frame = pl.DataFrame(data=series.data, orient="row")
            quotes = []
            i = 1
            for row in data_frame.rows(named=True):
                # Some values are missing, lets fill them re-using the last know value
                if row['column_0'] != i:
                    for j in range(i, row['column_0']):
                        # Even the first entry may be empty, in that case we need to use the provided value
                        value = quotes[-1] if len(quotes) > 0 else row['column_1']
                        quotes.append(value)
                        i += 1
                quotes.append(row['column_1'])
                i += 1

    return quotes

def import_products_quotation() -> None:
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
        
        # FIXME: Code copied from dashboard._create_products_quotation()
        # If the product is NOT tradable, we shouldn't consider it for Growth
        # The 'tradable' attribute identifies old Stocks, like the ones that are
        # renamed for some reason, and it's not good enough to identify stocks
        # that are provided as dividends, for example.
        if "Non tradeable" in product['name']:
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
        quotes = get_product_quotation(issueId, interval)
        dates = _calculate_dates(interval)
        quotes_dict = {}
        for count, date in enumerate(dates):
            # Keep only the dates that are in the quotation range
            from_date = product_growth[key]['quotation']['from_date']
            to_date = product_growth[key]['quotation']['to_date']
            if date >= datetime.strptime(from_date, DATE_FORMAT).date() and date <= datetime.strptime(to_date, DATE_FORMAT).date():
                quotes_dict[date.strftime(DATE_FORMAT)] = quotes[count]
        
        ProductQuotation.objects.update_or_create(
            id = int(key),
            defaults={'quotations': quotes_dict}
        )

def run():
    """
    Imports Product Information from DeGiro.
    """
    init()
    product_ids = get_productIds()
    get_products_info(product_ids, f"{IMPORT_FOLDER}/products_info.json")
    import_products_info(f"{IMPORT_FOLDER}/products_info.json")
    import_products_quotation()

if __name__ == '__main__':
    run()