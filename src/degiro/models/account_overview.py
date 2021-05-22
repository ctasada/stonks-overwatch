from typing import overload
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import format_money_value, get_base_currency_symbol, format_date_time

from trading.api import API as TradingAPI
from trading.pb.trading_pb2 import (
    Credentials,
    AccountOverview,
)
from datetime import date
import json

class AccountOverviewModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def get_account_overview(self):
        # SETUP REQUEST
        today = date.today()
        from_date = AccountOverview.Request.Date(
            year=2020,
            month=1,
            day=1,
        )
        to_date = AccountOverview.Request.Date(
            year=today.year,
            month=today.month,
            day=today.day,
        )
        request = AccountOverview.Request(
            from_date=from_date,
            to_date=to_date,
        )

        # FETCH DATA
        account_overview = self.deGiro.getClient().get_account_overview(
            request=request,
            raw=True,
        )

        # print(json.dumps(account_overview, indent = 4))

        overview = []
        for cash_movement in account_overview.get('data').get('cashMovements'):
            overview.append(
                dict(
                    date = format_date_time(cash_movement['date']),
                    valueDate = format_date_time(cash_movement['valueDate']),
                    description = cash_movement['description'],
                    type = cash_movement['type'],
                    currency = cash_movement['currency'],
                    change = cash_movement.get('change', ''),
                )
            )
        
        return overview