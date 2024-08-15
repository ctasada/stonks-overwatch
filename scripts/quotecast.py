# IMPORTATIONS

from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

import polars as pl
import common

from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.quotecast.models.chart import ChartRequest, Interval

# SETUP LOGGING
logging.basicConfig(level=logging.INFO)

# Retrieve user_token
trading_api = common.connectToDegiro()
client_details_table = trading_api.get_client_details()
int_account = client_details_table['data']['intAccount']
user_token = client_details_table['data']['id']

chart_fetcher = ChartFetcher(user_token=user_token)
chart_request = ChartRequest(
    culture="nl-NL",
    period=Interval.P5Y,
    requestid="1",
    resolution=Interval.P1D,
    series=[
        "issueid:350016959",
        "price:issueid:350016959",
    ],
    tz="Europe/Amsterdam",
)
chart = chart_fetcher.get_chart(
    chart_request=chart_request,
    raw=False,
)

for series in chart.series:
    print(pl.DataFrame(data=series.data, orient="row"))
    # if (series.type == 'time'):
    #     print(pl.DataFrame(data=series.data, orient="row"))

str_d1 = '2024/1/20'
# convert string to date object
d1 = datetime.strptime(str_d1, "%Y/%m/%d")
today = datetime.today()
# difference between dates in timedelta
delta = (today - d1).days
print(f'Difference is {delta} days')

match delta:
    case diff if diff in range(1, 7):
        print(Interval.P1W)
    case diff if diff in range(7, 30):
        print(Interval.P1M)
    case diff if diff in range(30, 90):
        print(Interval.P3M)
    case diff if diff in range(90, 180):
        print(Interval.P6M)
    case diff if diff in range(180, 365):
        print(Interval.P1Y)
    case diff if diff in range(365, 3 * 365):
        print(Interval.P3Y)
    case diff if diff in range(3 * 365, 5 * 365):
        print(Interval.P5Y)
    case diff if diff in range(5 * 365, 10 * 365):
        print(Interval.P10Y)

# Convert values to dates
start_date = today - relativedelta(days=31)
print(f"Today is {today.date()}")
print(start_date.date())
for i in range(1, 32):
    day = start_date + relativedelta(days=i)
    print(f'{i} - {day.date()}')
