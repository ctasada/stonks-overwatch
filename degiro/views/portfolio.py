from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from degiro.utils.degiro import DeGiro

import quotecast.helpers.pb_handler as pb_handler
from trading.pb.trading_pb2 import ProductsInfo, Update

import json

class Portfolio(View):
    def __init__(self):
        self.deGiro = DeGiro()

    def get(self, request):
        portfolio = self.__get_portfolio()
        print(portfolio)

        context = {
            "portfolio": portfolio,
        }

        return render(request, 'portfolio.html', context)

    def __get_portfolio(self):
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

        myPortfolio = []

        for portfolio in update_dict['portfolio']['values']:
            if portfolio['id'].isnumeric():
                info = products_info['data'][portfolio['id']]
                myPortfolio.append(
                    dict(
                        name=info['name'],
                        symbol = info['symbol'],
                        size = portfolio['size'],
                        price = portfolio['price'],
                        currency = info['currency'],
                        breakEvenPrice = portfolio['breakEvenPrice'], # GAK: Average Purchase Price                
                        value = portfolio['value'],
                        isin = info['isin'],
                        isOpen = (portfolio['size'] != 0.0 and portfolio['value'] != 0.0),
                    )
                )

        return sorted(myPortfolio, key=lambda k: k['symbol'])
