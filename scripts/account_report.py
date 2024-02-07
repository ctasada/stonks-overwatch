# IMPORTATIONS
import common
import json
import numpy as np
import pandas as pd

from datetime import date, datetime

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.account import Format, ReportRequest

trading_api = common.connectToDegiro()

# SETUP REQUEST
from_date = date(
    year=2020,
    month=1,
    day=1,
)

trading_api.connect()

# FETCH REPORT
report = trading_api.get_account_report(
    report_request=ReportRequest(
        country="NL",
        lang="en",
        format=Format.CSV,
        from_date=date(year=2020, month=1, day=1),
        to_date=date.today(),
    ),
    raw=False,
)

print(report)

csvFile = open("account.csv", "w")
csvFile.write(report.content)
csvFile.close()
