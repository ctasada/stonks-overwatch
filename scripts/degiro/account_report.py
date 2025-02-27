"""poetry run python ./scripts/degiro//account_report.py"""

# IMPORTATIONS
from datetime import date

import common
from degiro_connector.trading.models.account import Format, ReportRequest

trading_api = common.connect_to_degiro()

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

csv_file = open("account.csv", "w")
csv_file.write(report.content)
csv_file.close()
