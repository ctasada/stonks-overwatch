from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional

from currency_converter import CurrencyConverter

from stonks_overwatch.services.brokers.degiro.client.constants import CurrencyFX
from stonks_overwatch.services.brokers.degiro.repositories.product_quotations_repository import (
    ProductQuotationsRepository,
)
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.currency import get_standard_currency, normalize


@dataclass
class CurrencyMapEntry:
    product_id: int
    inverse: bool
    quotations: Optional[Dict[date, float]] = None


class CurrencyConverterService:
    logger = StonksLogger.get_logger("stonks_overwatch.currency_converter", "[DEGIRO|CURRENCY_CONVERTER]")

    def __init__(self):
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.known_currency_pairs = CurrencyFX.known_currencies()
        self.currency_maps = self.__calculate_maps()

    def convert(self, amount: float, currency: str, new_currency: str = "EUR", fx_date: datetime.date = None) -> float:
        """
        Convert an amount from one currency to another.

        Derived currencies (e.g. GBX pence) are normalised to their standard ISO
        equivalent before conversion. If new_currency is a derived currency it is
        also normalised, so the result is always in the standard (e.g. GBP), not
        the derived unit. Callers should never pass a derived currency as new_currency.

        Args:
            amount: The amount to convert.
            currency: Source currency code (may be a derived currency like GBX).
            new_currency: Target currency code. Must be a standard ISO code.
            fx_date: Optional date for the FX rate lookup.

        Returns:
            Converted amount in new_currency.
        """
        if amount is None:
            amount = 0.0

        # Normalize derived currencies (e.g. GBX pence → GBP pounds)
        amount, currency = normalize(amount, currency)
        new_currency = get_standard_currency(new_currency)

        # If both currencies are the same, no conversion is needed
        if currency == new_currency:
            return amount

        # If we know the currencies, we can use DeGiro's data
        if currency in self.known_currency_pairs and new_currency in self.known_currency_pairs:
            return self.__convert(amount, currency, new_currency, fx_date)

        # Fallback
        return self.currency_converter.convert(amount, currency, new_currency, fx_date)

    def __convert(self, amount: float, currency: str, new_currency: str, fx_date: date = None):
        if self.currency_maps[currency][new_currency].quotations is None:
            self.currency_maps[currency][new_currency].quotations = self.__load_quotations(currency, new_currency)

        quotations = self.currency_maps[currency][new_currency].quotations

        if not quotations:
            self.logger.debug(f"Empty quotations for {currency}/{new_currency}, falling back to currency_converter")
            return self.currency_converter.convert(amount, currency, new_currency, fx_date)

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

        if tmp_quotations is None:
            self.logger.warning(f"No quotations found for {currency}/{new_currency} (productId={product_id})")
            return {}

        return {
            LocalizationUtility.convert_string_to_date(date_str): value for date_str, value in tmp_quotations.items()
        }

    @staticmethod
    def __calculate_maps() -> Dict[str, Dict[str, CurrencyMapEntry]]:
        calculated_map = {}
        for pair in CurrencyFX:
            # Extract the currencies from the enum name
            base, quote = pair.name.split("_")
            product_id = pair.value
            calculated_map[base] = {quote: CurrencyMapEntry(product_id=product_id, inverse=False)}
            calculated_map[quote] = {base: CurrencyMapEntry(product_id=product_id, inverse=True)}

        return calculated_map
