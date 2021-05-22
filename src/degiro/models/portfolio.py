from degiro.utils.degiro import DeGiro
from degiro.utils.localization import format_money_value, get_base_currency_symbol

import quotecast.helpers.pb_handler as pb_handler
from trading.pb.trading_pb2 import ProductsInfo, Update

import json

class PortfolioModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def get_portfolio(self):
        # SETUP REQUEST
        request_list = Update.RequestList()
        request_list.values.extend([
            Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
        ])

        update = self.deGiro.getClient().get_update(request_list=request_list, raw=False)
        update_dict = pb_handler.message_to_dict(message=update)

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for portfolio in update_dict['portfolio']['values']:
            # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
            if portfolio['id'].isnumeric():
                products_ids.append(int(portfolio['id']))

        # SETUP REQUEST
        request = ProductsInfo.Request()
        request.products.extend(list(set(products_ids)))

        # FETCH DATA
        products_info = self.deGiro.getClient().get_products_info(
            request=request,
            raw=True,
        )

        # DEBUG Values
        # print(json.dumps(update_dict, indent = 4))
        # print(json.dumps(products_info, indent = 4))

        # Get user's base currency
        baseCurrencySymbol = get_base_currency_symbol()

        # print(accountInfo['data']['currencyPairs']['EURUSD']['price'])
        # print(update_dict['portfolio']['values'])
        myPortfolio = []

        for portfolio in update_dict['portfolio']['values']:
            if portfolio['id'].isnumeric():
                info = products_info['data'][portfolio['id']]
                company_profile = self.__get_company_profile(info['isin'])
                
                sector = 'Unknown'
                industry = 'Unknown'
                if company_profile.get('data'):
                    sector = company_profile['data']['sector']
                    industry = company_profile['data']['industry']

                price = format_money_value(value = portfolio['price'], currency = info['currency'])
                value = format_money_value(value = portfolio['value'], currencySymbol = baseCurrencySymbol)

                myPortfolio.append(
                    dict(
                        name=info['name'],
                        symbol = info['symbol'],
                        sector = sector,
                        industry = industry,
                        shares = portfolio['size'],
                        price = portfolio['price'],
                        formattedPrice = price,
                        breakEvenPrice = portfolio['breakEvenPrice'], # GAK: Average Purchase Price                
                        value = portfolio['value'],
                        formattedValue = value,
                        isOpen = (portfolio['size'] != 0.0 and portfolio['value'] != 0.0),
                    )
                )

        return sorted(myPortfolio, key=lambda k: k['symbol'])

    def __get_company_profile(self, product_isin):
        company_profile = self.deGiro.getClient().get_company_profile(
            product_isin=product_isin,
            raw=True,
        )

        return company_profile
