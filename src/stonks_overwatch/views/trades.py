from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.aggregators.trades_aggregator import TradesAggregatorService
from stonks_overwatch.services.models import dataclass_to_dict
from stonks_overwatch.services.utilities.session_manager import SessionManager


class Trades(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trades = TradesAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        retrieved_trades = self.trades.get_trades(selected_portfolio)
        # Pass Trade instances directly to the template for property access
        if request.headers.get("Accept") == "application/json":
            trades_data = [dataclass_to_dict(trade) for trade in retrieved_trades]
            return JsonResponse({"trades": trades_data}, safe=False)
        else:
            context = {"trades": retrieved_trades}
            return render(request, "trades.html", context)
