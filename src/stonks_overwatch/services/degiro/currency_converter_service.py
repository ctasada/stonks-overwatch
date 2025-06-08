from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional

from currency_converter import CurrencyConverter

from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository
from stonks_overwatch.services.degiro.constants import CurrencyFX
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger

@dataclass
class CurrencyMapEntry:
    product_id: int
    inverse: bool
    quotations: Optional[Dict[date, float]] = None

class CurrencyConverterService:
    logger = StonksLogger.get_logger("stonks_overwatch.currency_converter", "DEGIRO|CURRENCY_CONVERTER")

    def __init__(self):
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.known_currency_pairs = CurrencyFX.known_currencies()
        self.currency_maps = self.__calculate_maps()

    def convert(self, amount: float, currency: str, new_currency: str="EUR", fx_date: datetime.date=None) -> float:
        if amount is None:
            amount = 0.0

        # If both currencies are the same, no conversion is needed
        if currency == new_currency:
            return amount

        # If we know the currencies, we can use DeGiro's data
        if currency in self.known_currency_pairs and new_currency in self.known_currency_pairs:
            return self.__convert(amount, currency, new_currency, fx_date)

        # Fallback
        return self.currency_converter.convert(amount, currency, new_currency, fx_date)

    def __convert(self, amount: float, currency: str, new_currency: str, fx_date: date=None):
        if self.currency_maps[currency][new_currency].quotations is None:
            self.currency_maps[currency][new_currency].quotations = self.__load_quotations(currency, new_currency)

        quotations = self.currency_maps[currency][new_currency].quotations

        last_known_date = list(quotations.keys())[-1]
        if fx_date is None or fx_date > last_known_date:
            fx_date = last_known_date

        fx_rate = quotations[fx_date]

        if fx_rate is None:
            self.logger.warning(f"Cannot find FX rate for {currency}/{new_currency} on {fx_date}")
            return self.currency_converter.convert(amount, currency, new_currency, fx_date)

        if self.currency_maps[currency][new_currency].inverse:
            return amount * (1 / fx_rate)

        return amount * fx_rate

    def __load_quotations(self, currency: str, new_currency: str) -> Dict[date, float]:
        product_id = self.currency_maps[currency][new_currency].product_id
        tmp_quotations = ProductQuotationsRepository.get_product_quotations(product_id)

        return {
            LocalizationUtility.convert_string_to_date(date_str): value
            for date_str, value in tmp_quotations.items()
        }

    @staticmethod
    def __calculate_maps() -> Dict[str, Dict[str, CurrencyMapEntry]]:
        calculated_map = {}
        for pair in CurrencyFX:
            # Extract the currencies from the enum name
            base, quote = pair.name.split('_')
            product_id = pair.value
            calculated_map[base] = {
                quote: CurrencyMapEntry(product_id=product_id, inverse=False)
            }
            calculated_map[quote] = {
                base: CurrencyMapEntry(product_id=product_id, inverse=True)
            }

        return calculated_map
