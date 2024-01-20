# IMPORTATIONS
import common
import json

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

trading_api = common.connectToDegiro()

# SETUP REQUEST
update = trading_api.get_update(
    request_list=[
        UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
    ],
    raw=True,
)
# total_portfolio_df = pd.DataFrame(update_dict['total_portfolio']['values'])

print(json.dumps(update, indent = 4))

# DISPLAY CASH MOVEMENTS
# for cash_movement in account_overview.values['cashMovements']:
    # print('date:', cash_movement['date'])
    # print('valueDate:', cash_movement['valueDate'])
    # print('productId:', dict(cash_movement).get('productId', 'unknown'))
    # print('currency:', dict(cash_movement).get('currency', 'unknown'))
    # print('change:', dict(cash_movement).get('change', 'unknown'))
    # print(cash_movement)
    # break

trading_api.logout()