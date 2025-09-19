"""poetry run python -m scripts.degiro.company_profile"""

# IMPORTATIONS
import json

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# FETCH DATA
product_isin = "US0378331005"
company_profile = trading_api.get_company_profile(
    product_isin=product_isin,
    raw=True,
)

# DISPLAY DATA
print(json.dumps(company_profile, indent=4))
trading_api.logout()
