from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

import degiro_connector.core.helpers.pb_handler as pb_handler
from degiro_connector.trading.models.trading_pb2 import Update

import json

class PortfolioModel:

    def get_portfolio(self):
        # SETUP REQUEST
        request_list = Update.RequestList()
        request_list.values.extend([
            Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
        ])

        update = DeGiro.get_client().get_update(request_list=request_list, raw=False)
        update_dict = pb_handler.message_to_dict(message=update)

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for portfolio in update_dict['portfolio']['values']:
            # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
            if portfolio['id'].isnumeric():
                products_ids.append(int(portfolio['id']))

        products_info = DeGiro.get_products_info(products_ids)

        # DEBUG Values
        # print(json.dumps(update_dict, indent = 4))

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        myPortfolio = []

        for portfolio in update_dict['portfolio']['values']:
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
        portfolio = self.get_portfolio()

        portfolioTotalValue = 0.0

        for equity in portfolio:
            portfolioTotalValue += equity['value']

        return portfolioTotalValue

    def __get_company_profile(self, product_isin):
        company_profile = DeGiro.get_client().get_company_profile(
            product_isin=product_isin,
            raw=True,
        )

        return company_profile
