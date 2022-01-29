from typing import overload
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import (
    Credentials,
    AccountOverview,
)
from datetime import date
import json

class AccountOverviewModel:

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
        account_overview = DeGiro.get_client().get_account_overview(
            request=request,
            raw=True,
        )

        products_ids = []
        for cash_movement in account_overview.get('data').get('cashMovements'):
            if 'productId' in cash_movement:
                products_ids.append(int(cash_movement['productId']))

        products_info = DeGiro.get_products_info(products_ids)
        
        # print(json.dumps(account_overview, indent = 4))

        overview = []
        for cash_movement in account_overview.get('data').get('cashMovements'):
            
            stockName = ''
            stockSymbol = ''
            if 'productId' in cash_movement:
                info = products_info[str(int(cash_movement['productId']))]
                stockName = info['name']
                stockSymbol = info['symbol']

            formatedChange = ''
            if 'change' in cash_movement:
                formatedChange = LocalizationUtility.format_money_value(value = cash_movement['change'], currency = cash_movement['currency'])
            
            unsettledCash = 0
            formatedUnsettledCash = ''
            formatedTotalBalance = ''
            totalBalance = 0
            if 'balance' in cash_movement:
                totalBalance = cash_movement.get('balance').get('total')
                formatedTotalBalance = LocalizationUtility.format_money_value(value = totalBalance, currency = cash_movement['currency'])
                unsettledCash = cash_movement.get('balance').get('unsettledCash')
                formatedUnsettledCash = LocalizationUtility.format_money_value(value = unsettledCash, currency = cash_movement['currency'])
            
            overview.append(
                dict(
                    date = LocalizationUtility.format_date_time(cash_movement['date']),
                    valueDate = LocalizationUtility.format_date_time(cash_movement['valueDate']),
                    stockName = stockName,
                    stockSymbol = stockSymbol,
                    description = cash_movement['description'],
                    type = cash_movement['type'],
                    typeStr = cash_movement['type'].replace("_", " ").title(),
                    currency = cash_movement['currency'],
                    change = cash_movement.get('change', ''),
                    formatedChange = formatedChange,
                    totalBalance = totalBalance,
                    formatedTotalBalance = formatedTotalBalance,
                    # Seems that this value is the proper one for Dividends. Checking ...
                    unsettledCash = unsettledCash,
                    formatedUnsettledCash = formatedUnsettledCash,
                )
            )
        
        return overview

    def get_dividends(self):
        overview = self.get_account_overview()

        dividends = []
        for transaction in overview:
            # We don't include 'Dividendbelasting' because the 'value' seems to already include the taxes
            if (transaction['description'] in ['Dividend', 'Vermogenswinst']):
                dividends.append(transaction)

        return dividends