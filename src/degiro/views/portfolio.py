from django.views import View
from django.shortcuts import render

from degiro.integration.portfolio import PortfolioData


class Portfolio(View):
    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        # print (json.dumps(portfolio, indent=2))

        context = {
            "portfolio": portfolio,
        }

        return render(request, 'portfolio.html', context)
