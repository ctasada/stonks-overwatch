"""Base service for all Alpaca Markets services that require currency conversion."""

from datetime import date
from typing import Optional

from currency_converter import CurrencyConverter

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.utils.core.logger import StonksLogger


class AlpacaBaseService(BaseService):
    """
    Intermediate base class for Alpaca services that handle monetary amounts.

    Centralises three pieces of logic that would otherwise be duplicated in every
    Alpaca service:

    * ``BROKER_CURRENCY`` — the native currency of all Alpaca API amounts (USD).
    * ``self._fx`` — a shared ``CurrencyConverter`` instance.
    * ``_to_base(amount, on_date)`` — a single conversion helper that accepts an
      optional *on_date* argument.  When *on_date* is supplied the historical rate
      for that date is used (suitable for past transactions); when omitted the
      current spot rate is used (suitable for live prices).

    Subclasses only need to call ``super().__init__(config, **kwargs)`` and can
    then call ``self._to_base(...)`` directly without redeclaring the converter.
    """

    BROKER_CURRENCY: str = "USD"

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.base", "[ALPACA|BASE]")

    def __init__(self, config: Optional[AlpacaConfig] = None, **kwargs) -> None:
        """
        Initialise the base service and the shared FX converter.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
            **kwargs: Forwarded to BaseService
        """
        super().__init__(config, **kwargs)
        self._fx = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def _to_base(self, amount: float, on_date: Optional[date] = None) -> float:
        """
        Convert a USD amount to the user's base currency.

        When *on_date* is provided the historical exchange rate for that date is
        used, which is appropriate for past transactions (deposits, dividends,
        fills).  When omitted the current spot rate is used, which is appropriate
        for live market prices.

        If base_currency is already USD the amount is returned unchanged without
        hitting the converter.  FX failures fall back to the original USD amount
        and emit a WARNING log so callers always receive a usable value.

        Args:
            amount: Amount denominated in ``BROKER_CURRENCY`` (USD).
            on_date: Optional transaction date for historical rate lookup.

        Returns:
            Amount converted to ``self.base_currency``.
        """
        if self.base_currency == self.BROKER_CURRENCY:
            return amount
        try:
            if on_date:
                return self._fx.convert(amount, self.BROKER_CURRENCY, self.base_currency, date=on_date)
            return self._fx.convert(amount, self.BROKER_CURRENCY, self.base_currency)
        except Exception as e:
            self.logger.warning(f"FX conversion failed for {amount} {self.BROKER_CURRENCY} on {on_date}: {e}")
            return amount
