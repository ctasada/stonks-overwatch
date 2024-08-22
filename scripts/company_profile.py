"""
poetry run python ./scripts/company_profile.py
"""
# IMPORTATIONS
import common
import json


trading_api = common.connectToDegiro()

# FETCH DATA
product_isin = 'US0378331005'
company_profile = trading_api.get_company_profile(
    product_isin=product_isin,
    raw=True,
)

# DISPLAY DATA
print(json.dumps(company_profile, indent=4))
trading_api.logout()
