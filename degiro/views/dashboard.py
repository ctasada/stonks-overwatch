from django.views import View
from django.shortcuts import render

from degiro.models.portfolio import PortfolioModel

import json

class Dashboard(View):
    def __init__(self):
        self.portfolio = PortfolioModel()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        # print (json.dumps(portfolio, indent=2))

        sectors = {}

        for stock in portfolio:
            if stock['isOpen']:
                sectorName = stock['sector']
                sectors[sectorName] = stock.get("value", 0) + stock['value']

        labels = []
        values = []
        for key in sectors:
            labels.append(key)
            values.append(sectors[key])

        context = {
            "labels": labels,
            "values": values,
        }

        return render(request, 'dashboard.html', context)
