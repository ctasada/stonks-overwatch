from degiro.utils.degiro import DeGiro
from currency_symbols import CurrencySymbols
import datetime

class LocalizationUtility(object):
    # Get user's base currency
    @staticmethod
    def get_base_currency_symbol():
        accountInfo = DeGiro.get_account_info()
        baseCurrency = accountInfo['data']['baseCurrency']
        baseCurrencySymbol = CurrencySymbols.get_symbol(baseCurrency)

        return baseCurrencySymbol

    @staticmethod
    def format_money_value(value: float, currency: str = None, currencySymbol : str = None):
        if (currency and not currencySymbol):
            currencySymbol = CurrencySymbols.get_symbol(currency)
        
        return currencySymbol + " {:,.2f}".format(value)

    @staticmethod
    def format_date_time(value: str):
        time = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
        return time.strftime('%Y-%m-%d %H:%M:%S')