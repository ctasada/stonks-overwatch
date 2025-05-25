from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.fees_aggregator import FeesAggregatorService
from stonks_overwatch.services.session_manager import SessionManager
from stonks_overwatch.utils.localization import LocalizationUtility

class Fees(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fees = FeesAggregatorService()
        self.base_currency = "EUR"

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        fees = self.fees.get_fees(selected_portfolio)
        base_currency_symbol = LocalizationUtility.get_currency_symbol(self.base_currency)
        transaction_fees = 0
        exchange_fees = 0
        ftt_fees = 0
        adr_fees = 0
        for fee in fees:
            if fee["type"] == "Transaction":
                transaction_fees += fee["fee_value"]
            elif fee["type"] == "Finance Transaction Tax":
                ftt_fees += fee["fee_value"]
            elif fee["type"] == "Connection":
                exchange_fees += fee["fee_value"]
            elif fee["type"] == "ADR/GDR":
                adr_fees += fee["fee_value"]

        context = {
            "transaction_fees": LocalizationUtility.format_money_value(
                value=transaction_fees, currency_symbol=base_currency_symbol
            ),
            "exchange_fees": LocalizationUtility.format_money_value(
                value=exchange_fees, currency_symbol=base_currency_symbol
            ),
            "ftt_fees": LocalizationUtility.format_money_value(value=ftt_fees, currency_symbol=base_currency_symbol),
            "adr_fees": LocalizationUtility.format_money_value(value=adr_fees, currency_symbol=base_currency_symbol),
            "fees": fees,
        }

        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(context, safe=False)
        else:
            return render(request, "fees.html", context)
