from degiro.utils.degiro import DeGiro
from currency_symbols import CurrencySymbols

# Get user's base currency
def get_base_currency_symbol():
    deGiro = DeGiro()
    accountInfo = deGiro.get_account_info()
    baseCurrency = accountInfo['data']['baseCurrency']
    baseCurrencySymbol = CurrencySymbols.get_symbol(baseCurrency)

    return baseCurrencySymbol

def format_money_value(value: float, currency: str = None, currencySymbol : str = None):
    if (currency and not currencySymbol):
        currencySymbol = CurrencySymbols.get_symbol(currency)
    
    return currencySymbol + " {:,.2f}".format(value)