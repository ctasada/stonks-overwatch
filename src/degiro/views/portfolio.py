from django.views import View
from django.shortcuts import render

from degiro.data.portfolio import PortfolioData


class Portfolio(View):
    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()

        context = {
            "portfolio": portfolio,
        }

        return render(request, 'portfolio.html', context)
