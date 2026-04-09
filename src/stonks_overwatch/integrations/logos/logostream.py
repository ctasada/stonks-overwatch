from urllib.parse import quote

import requests
from requests.exceptions import RequestException

from stonks_overwatch.integrations.logos.base import LogoIntegration
from stonks_overwatch.integrations.logos.types import LogoType
from stonks_overwatch.utils.core.logger import StonksLogger


class LogostreamIntegration(LogoIntegration):
    STOCK_SYMBOL_URL = "https://api.logostream.dev/stocks/symbol/{symbol}?key={key}&variant=default&format=svg"
    STOCK_ISIN_URL = "https://api.logostream.dev/stocks/isin/{isin}?key={key}&variant=default&format=svg"
    CRYPTO_URL = "https://api.logostream.dev/cryptos/{symbol}?key={key}&variant=default&format=svg"
    FOREX_URL = "https://api.logostream.dev/forex/{currency_code}?key={key}&variant=default&format=svg"
    COUNTRY_URL = "https://api.logostream.dev/country/{country_code}?key={key}&variant=default&format=svg"

    logger = StonksLogger.get_logger("stonks_overwatch.integrations.logos", "[LOGOSTREAM|LOGO]")

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def is_active(self) -> bool:
        return bool(self._api_key)

    def supports(self, logo_type: LogoType) -> bool:
        return logo_type in {LogoType.STOCK, LogoType.ETF, LogoType.CRYPTO, LogoType.CASH, LogoType.COUNTRY}

    def get_logo_url(
        self, logo_type: LogoType, symbol: str, theme: str = "light", isin: str = "", conid: str = ""
    ) -> str:
        """Build and validate the Logostream URL for the given asset.

        Performs a streaming GET request to confirm the logo exists before returning the URL.
        Returns ``""`` if the logo is not available, allowing the caller to fall through
        to the next integration or the CDN fallback.

        Args:
            logo_type: The type of asset (STOCK, ETF, CRYPTO, CASH, or COUNTRY).
            symbol: The asset ticker or crypto symbol.
            theme: Display theme (unused by Logostream — included for interface compatibility).
            isin: ISIN code. When provided for stocks/ETFs, used instead of the symbol for
                better accuracy.
            conid: IBKR contract ID (unused by this integration).

        Returns:
            A fully qualified Logostream URL string, or ``""`` if the logo does not exist.
        """
        if logo_type == LogoType.CRYPTO:
            url = self.CRYPTO_URL.format(symbol=quote(symbol.lower()), key=self._api_key)
        elif logo_type == LogoType.CASH:
            url = self.FOREX_URL.format(currency_code=quote(symbol.upper()), key=self._api_key)
        elif logo_type == LogoType.COUNTRY:
            country_code = self._normalize_country_code(symbol)
            url = self.COUNTRY_URL.format(country_code=quote(country_code), key=self._api_key)
        elif isin:
            url = self.STOCK_ISIN_URL.format(isin=quote(isin.upper()), key=self._api_key)
        else:
            url = self.STOCK_SYMBOL_URL.format(symbol=quote(symbol.upper()), key=self._api_key)

        try:
            response = requests.get(url, timeout=3, stream=True)
            response.close()
            if response.status_code >= 400:
                self.logger.debug(f"Logostream returned {response.status_code} for {symbol.upper()}")
                return ""
        except RequestException as e:
            self.logger.debug(f"Logostream availability check failed for {symbol.upper()}: {e}")
            return ""

        return url

    @staticmethod
    def _normalize_country_code(symbol: str) -> str:
        """Normalize country inputs to ISO-3166 alpha-2 codes when possible."""
        if len(symbol) == 2 and symbol.isalpha():
            return symbol.upper()

        letters = []
        for char in symbol:
            codepoint = ord(char)
            if 0x1F1E6 <= codepoint <= 0x1F1FF:
                letters.append(chr(codepoint - 0x1F1E6 + ord("A")))
            else:
                return symbol.upper()

        return "".join(letters) if letters else symbol.upper()
