from datetime import datetime

from currency_converter import CurrencyConverter

from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository
from stonks_overwatch.services.degiro.constants import CurrencyFX
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger

class CurrencyConverterService:
    logger = StonksLogger.get_logger("stocks_portfolio.currency_converter", "DEGIRO|CURRENCY_CONVERTER")

    def __init__(self):
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.known_currency_pairs = CurrencyFX.known_currencies()
        self.currency_maps = self.__calculate_maps()

    def convert(self, amount: float, currency: str, new_currency: str="EUR", date: datetime.date=None) -> float:
        # If both currencies are the same, no conversion is needed
        if currency == new_currency:
            return amount

        # If we know the currencies, we can use DeGiro's data
        if currency in self.known_currency_pairs and new_currency in self.known_currency_pairs:
            return self.__convert(amount, currency, new_currency, date)

        # Fallback
        return self.currency_converter.convert(amount, currency, new_currency, date)

    def __convert(self, amount: float, currency: str, new_currency: str, date: datetime.date=None):
        product_id = self.currency_maps[currency][new_currency]["productId"]
        quotations = ProductQuotationsRepository.get_product_quotations(product_id)

        last_known_date = LocalizationUtility.convert_string_to_date(list(quotations.keys())[-1])
        if date is None or date > last_known_date:
            date = last_known_date

        fx_rate = quotations[date.strftime("%Y-%m-%d")]

        if fx_rate is None:
            self.logger.warning(f"Cannot find FX rate for {currency}/{new_currency} on {date}")
            return self.currency_converter.convert(amount, currency, new_currency, date)

        if self.currency_maps[currency][new_currency]["inverse"]:
            return amount * (1 / fx_rate)

        return amount * fx_rate

    @staticmethod
    def __calculate_maps() -> dict:
        calculated_map = {}
        for pair in CurrencyFX:
            # Extract the currencies from the enum name
            base, quote = pair.name.split('_')
            product_id = pair.value
            calculated_map[base] = {
                quote: {
                    "productId": product_id,
                    "inverse": False
                }
            }
            calculated_map[quote] = {
                base: {
                    "productId": product_id,
                    "inverse": True
                }
            }

        return calculated_map
