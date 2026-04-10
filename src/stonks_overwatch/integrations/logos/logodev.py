from urllib.parse import quote

import requests
from requests.exceptions import RequestException

from stonks_overwatch.integrations.logos.base import LogoIntegration
from stonks_overwatch.integrations.logos.types import LogoType
from stonks_overwatch.utils.core.logger import StonksLogger


class LogoDevIntegration(LogoIntegration):
    ISIN_URL = (
        "https://img.logo.dev/isin/{isin}?token={token}&theme={theme}&format=png&size=256&retina=true&fallback=404"
    )
    STOCK_URL = (
        "https://img.logo.dev/ticker/{symbol}?token={token}&theme={theme}&format=png&size=256&retina=true&fallback=404"
    )
    CRYPTO_URL = (
        "https://img.logo.dev/crypto/{symbol}?token={token}&theme={theme}&format=png&size=256&retina=true&fallback=404"
    )

    logger = StonksLogger.get_logger("stonks_overwatch.integrations.logos", "[LOGODEV|LOGO]")

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def is_active(self) -> bool:
        return bool(self._api_key)

    def supports(self, logo_type: LogoType) -> bool:
        return logo_type in {LogoType.STOCK, LogoType.ETF, LogoType.CRYPTO}

    def get_logo_url(
        self, logo_type: LogoType, symbol: str, theme: str = "light", isin: str = "", conid: str = ""
    ) -> str:
        """Build and validate the Logo.dev URL for the given asset.

        Performs a streaming GET request to confirm the logo exists before returning the URL.
        HEAD is not used as Logo.dev's CDN does not support it reliably. The ``fallback=404``
        parameter ensures Logo.dev returns a real 404 (rather than a generated monogram) when
        no logo exists for the requested symbol.
        Returns ``""`` if the logo is not available, allowing the caller to fall through
        to the next integration or the CDN fallback.

        Args:
            logo_type: The type of asset (STOCK, ETF, or CRYPTO).
            symbol: The asset ticker or crypto symbol.
            theme: Display theme — ``"dark"`` selects a dark-background logo variant.
            isin: ISIN code. When provided for stocks/ETFs, used instead of symbol for better accuracy.
            conid: IBKR contract ID (unused by this integration).

        Returns:
            A fully qualified Logo.dev URL string, or ``""`` if the logo does not exist.
        """
        if logo_type == LogoType.CRYPTO:
            url = self.CRYPTO_URL.format(symbol=quote(symbol.lower()), token=self._api_key, theme=theme)
        elif isin:
            url = self.ISIN_URL.format(isin=quote(isin.upper()), token=self._api_key, theme=theme)
        else:
            url = self.STOCK_URL.format(symbol=quote(symbol.upper()), token=self._api_key, theme=theme)

        try:
            response = requests.get(url, timeout=3, stream=True)
            response.close()
            if response.status_code >= 400:
                self.logger.debug(f"Logo.dev returned {response.status_code} for {symbol.upper()}")
                return ""
        except RequestException as e:
            self.logger.debug(f"Logo.dev availability check failed for {symbol.upper()}: {e}")
            return ""

        return url
