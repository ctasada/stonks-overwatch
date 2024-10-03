from django.shortcuts import render
from django.views import View

from degiro.services.fees import FeesService
from degiro.utils.localization import LocalizationUtility


class Fees(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fees = FeesService()

    def get(self, request):
        fees = self.fees.get_fees()

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
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

        return render(request, "fees.html", context)
