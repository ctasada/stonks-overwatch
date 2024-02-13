import array
import json
import polars as pl
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.db import connection
from django.forms import model_to_dict
from degiro.utils.db_utils import dictfetchall
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.quotecast.models.chart import ChartRequest, Interval

from degiro.utils.degiro import DeGiro

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

def get_productInfo(productId) -> dict:
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
    # Convert String to date object
    d1 = datetime.strptime(date_from, "%Y-%m-%d")
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

def _calculate_delta(interval) -> int:
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

def _calculate_dates(interval) -> array:
    # Convert values to dates
    today = datetime.today().date()
    days = _calculate_delta(interval)
    start_date = today - relativedelta(days=days)
    result = []
    for i in range(1, days):
        day = start_date + relativedelta(days=i)
        result.append(day)
    
    return result

def _get_quotation(issueid, period):
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
        final_date = datetime.today().strftime('%Y-%m-%d')
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
        quotes = _get_quotation(issueId, interval)
        dates = _calculate_dates(interval)
        quotes_dict = {}
        for count, date in enumerate(dates):
            # Keep only the dates that are in the quotation range
            from_date = product_growth[key]['quotation']['from_date']
            to_date = product_growth[key]['quotation']['to_date']
            if date >= datetime.strptime(from_date, '%Y-%m-%d').date() and date <= datetime.strptime(to_date, '%Y-%m-%d').date():
                quotes_dict[date.strftime('%Y-%m-%d')] = quotes[count]
        
        product_growth[key]['quotation']['quotes'] = quotes_dict

    data_file = open('./import/transform.json', 'w')
    data_file.write(json.dumps(product_growth, indent = 4))
    data_file.close()

    # With everything now we need to calculate the daily aggregate

    # print(json.dumps(product_growth, indent = 4))


def _calculate_position_growth(entry: dict) -> dict:
    print(f"Processing {entry['product']['name']}")
    
    product_history_dates = list(entry['history'].keys())
    
    start_date = datetime.strptime(product_history_dates[0], '%Y-%m-%d').date()
    if product_history_dates[-1] == 0:
        final_date = datetime.strptime(product_history_dates[-1], '%Y-%m-%d').date()
    else:
        final_date = datetime.today().date()

    # difference between current and previous date
    delta = timedelta(days=1)
    # store the dates between two dates in a list
    dates = []
    while start_date <= final_date:
        # add current date to list by converting  it to iso format
        dates.append(start_date.strftime('%Y-%m-%d'))
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

def _calculate_growth(json_file_path) -> None:
    with open(json_file_path) as json_file:
        data = json.load(json_file)

    # FIXME: Maybe Pandas/Polar provides a better way
    # FIXME: We need to convert USD/EUR, here we ignore the currency
    # FIXME: The result is off by more than 4K, maybe due to FX
    aggregate = dict()
    for key in data:
        entry = data[key]
        position_value_growth = _calculate_position_growth(entry)
        for date in position_value_growth:
            aggregate_value = aggregate.get(date, 0)
            aggregate_value += position_value_growth[date]
            aggregate[date] = aggregate_value

    data_file = open('./import/aggregate_value.json', 'w')
    data_file.write(json.dumps(aggregate, indent = 4))
    data_file.close()

def run():
    # get_productIds()
    # get_value_growth()
    _calculate_growth('./import/transform.json')

if __name__ == '__main__':
    run()