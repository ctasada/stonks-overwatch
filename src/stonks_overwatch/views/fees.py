from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.aggregators.fees_aggregator import FeesAggregatorService
from stonks_overwatch.services.models import FeeType
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class Fees(View):
    logger = StonksLogger.get_logger("stonks_overwatch.fees.views", "[VIEW|FEES]")

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
            if fee.type == FeeType.TRANSACTION:
                transaction_fees += fee.fee_value
            elif fee.type == FeeType.FINANCE_TRANSACTION_TAX:
                ftt_fees += fee.fee_value
            elif fee.type == FeeType.CONNECTION:
                exchange_fees += fee.fee_value
            elif fee.type == FeeType.ADR_GDR:
                adr_fees += fee.fee_value

        context = {
            "transaction_fees": LocalizationUtility.format_money_value(
                value=transaction_fees, currency_symbol=base_currency_symbol
            ),
            "exchange_fees": LocalizationUtility.format_money_value(
                value=exchange_fees, currency_symbol=base_currency_symbol
            ),
            "ftt_fees": LocalizationUtility.format_money_value(value=ftt_fees, currency_symbol=base_currency_symbol),
            "adr_fees": LocalizationUtility.format_money_value(value=adr_fees, currency_symbol=base_currency_symbol),
            "fees": [fee.to_dict() for fee in fees],
        }

        if request.headers.get("Accept") == "application/json":
            return JsonResponse(context, safe=False)
        else:
            return render(request, "fees.html", context)
