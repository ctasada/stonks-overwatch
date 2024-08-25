from django.views import View
from django.shortcuts import render

from degiro.data.fees import FeesData
from degiro.utils.localization import LocalizationUtility


class Fees(View):
    def __init__(self):
        self.fees = FeesData()

    def get(self, request):
        fees = self.fees.get_fees()

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
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
                value=transaction_fees,
                currencySymbol=baseCurrencySymbol
            ),
            "exchange_fees": LocalizationUtility.format_money_value(
                value=exchange_fees,
                currencySymbol=baseCurrencySymbol
            ),
            "ftt_fees": LocalizationUtility.format_money_value(
                value=ftt_fees,
                currencySymbol=baseCurrencySymbol
            ),
            "adr_fees": LocalizationUtility.format_money_value(
                value=adr_fees,
                currencySymbol=baseCurrencySymbol
            ),
            "fees": fees,
        }

        return render(request, 'fees.html', context)
