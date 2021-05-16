from django.views import View
from django.shortcuts import render

from degiro.models.portfolio import PortfolioModel

import json

class Dashboard(View):
    def __init__(self):
        self.portfolio = PortfolioModel()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        portfolio = sorted(portfolio, key=lambda k: k['sector'])
        # print (json.dumps(portfolio, indent=2))

        sectors = {}

        stockLabels = []
        stockValues = []

        for stock in portfolio:
            if stock['isOpen']:
                sectorName = stock['sector']
                sectors[sectorName] = sectors.get(sectorName, 0) + stock['value']
                stockLabels.append(stock['symbol'])
                stockValues.append(stock['value'])

        sectorLabels = []
        sectorValues = []
        for key in sectors:
            sectorLabels.append(key)
            sectorValues.append(sectors[key])

        context = {
            "labels": sectorLabels + stockLabels,
            "sectors": {
                "labels": sectorLabels,
                "values": sectorValues,
            },
            "stocks": {
                "labels": stockLabels,
                "values": stockValues,
            },
            "currencySymbol": self.portfolio.get_base_currency_symbol(),
        }
        
        return render(request, 'dashboard.html', context)
