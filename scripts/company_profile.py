# IMPORTATIONS
import common
import json

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

trading_api = common.connectToDegiro()

# FETCH DATA
product_isin = 'US0378331005'
company_profile = trading_api.get_company_profile(
    product_isin=product_isin,
    raw=True,
)

# DISPLAY DATA
print(json.dumps(company_profile, indent = 4))
trading_api.logout()