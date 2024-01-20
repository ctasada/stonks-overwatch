from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

import json

class PortfolioModel:

    def get_portfolio(self):
        # SETUP REQUEST
        update = DeGiro.get_client().get_update(request_list=[
            UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
        ], raw=True)

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for portfolio in update['portfolio']['value']:
            # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
            if portfolio['id'].isnumeric():
                products_ids.append(int(portfolio['id']))

        products_info = DeGiro.get_products_info(products_ids)

        # DEBUG Values
        # print(json.dumps(update_dict, indent = 4))

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        myPortfolio = []

        for tmp in update['portfolio']['value']:
            # Portfolio has a weird structure, lets convert it here
            portfolio = {}
            for value in tmp['value']:
                if value.get("value") is not None:
                    portfolio[value['name']] = value['value']
            # Finish conversion
            if portfolio['id'].isnumeric():
                info = products_info[portfolio['id']]
                company_profile = self.__get_company_profile(info['isin'])
                
                sector = 'Unknown'
                industry = 'Unknown'
                if company_profile.get('data'):
                    sector = company_profile['data']['sector']
                    industry = company_profile['data']['industry']

                price = LocalizationUtility.format_money_value(value = portfolio['price'], currency = info['currency'])
                value = LocalizationUtility.format_money_value(value = portfolio['value'], currencySymbol = baseCurrencySymbol)
                breakEvenPrice = LocalizationUtility.format_money_value(value = portfolio['breakEvenPrice'], currency = info['currency'])

                unrealizedGain = (portfolio['price'] - portfolio['breakEvenPrice']) * portfolio['size']
                formattedUnrealizedGain = LocalizationUtility.format_money_value(value = unrealizedGain, currency = info['currency'])

                myPortfolio.append(
                    dict(
                        name=info['name'],
                        symbol = info['symbol'],
                        sector = sector,
                        industry = industry,
                        shares = portfolio['size'],
                        price = portfolio['price'],
                        breakEvenPrice = portfolio['breakEvenPrice'],
                        formattedPrice = price,
                        formattedBreakEvenPrice = breakEvenPrice, # GAK: Average Purchase Price
                        value = portfolio['value'],
                        formattedValue = value,
                        isOpen = (portfolio['size'] != 0.0 and portfolio['value'] != 0.0),
                        unrealizedGain = unrealizedGain,
                        formattedUnrealizedGain = formattedUnrealizedGain,
                    )
                )

        return sorted(myPortfolio, key=lambda k: k['symbol'])

    def get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolioTotalValue = 0.0

        for equity in portfolio:
            portfolioTotalValue += equity['value']
        
        # SETUP REQUEST
        update = DeGiro.get_client().get_update(
            request_list=[
                UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
            ],
            raw=True,
        )

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
        # print(json.dumps(update_dict, indent = 4))

        # Portfolio has a weird structure, lets convert it here
        tmp_total_portfolio = {}
        for value in update['totalPortfolio']['value']:
            if value.get("value") is not None:
                tmp_total_portfolio[value['name']] = value['value']
        # Finish conversion

        total_portfolio = {
            "totalDepositWithdrawal": LocalizationUtility.format_money_value(value = tmp_total_portfolio['totalDepositWithdrawal'], currencySymbol = baseCurrencySymbol),
            "totalCash": LocalizationUtility.format_money_value(value = tmp_total_portfolio['totalCash'], currencySymbol = baseCurrencySymbol),
            "currentValue": LocalizationUtility.format_money_value(value = portfolioTotalValue, currencySymbol = baseCurrencySymbol)
        }

        return total_portfolio

    def __get_company_profile(self, product_isin):
        company_profile = DeGiro.get_client().get_company_profile(
            product_isin=product_isin,
            raw=True,
        )

        return company_profile
