from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException

from stonks_overwatch.integrations.logos.base import LogoIntegration
from stonks_overwatch.integrations.logos.types import LogoType
from stonks_overwatch.utils.core.logger import StonksLogger


class IbkrLogoIntegration(LogoIntegration):
    """Logo integration that resolves asset icons via Interactive Brokers' internal Benzinga proxy.

    This uses an undocumented IBKR endpoint — it is not part of any public API contract
    and may change or be removed without notice. The lookup key is the IBKR contract ID
    (``conid``), which is only available for assets held in an IBKR account.
    """

    # Undocumented IBKR proxy that forwards requests to Benzinga's icon CDN.
    # Only available for authenticated IBKR sessions; used here for browser-side hotlinking.
    BASE_URL = "https://www.interactivebrokers.ie/tws.proxy/public/icons/benzinga"

    logger = StonksLogger.get_logger("stonks_overwatch.integrations.logos", "[IBKR|LOGO]")

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    def is_active(self) -> bool:
        return self._enabled

    def supports(self, logo_type: LogoType) -> bool:
        """Return True for asset types that IBKR's Benzinga proxy covers."""
        return logo_type in {LogoType.STOCK, LogoType.ETF}

    def get_logo_url(
        self, logo_type: LogoType, symbol: str, theme: str = "light", isin: str = "", conid: str = ""
    ) -> str:
        """Build and validate the Benzinga proxy URL for the given contract ID.

        Uses a streaming GET (not HEAD) because the Benzinga proxy does not reliably support
        HEAD requests. The stream is closed immediately after checking the status code to avoid
        downloading the full image. Returns ``""`` if the icon is not available, allowing the
        caller to fall through to the next integration or the CDN fallback.

        Args:
            logo_type: The type of asset (must be STOCK or ETF).
            symbol: The asset ticker symbol (unused; IBKR uses conid as the key).
            theme: Display theme — ``"dark"`` selects a dark-background icon variant.
            isin: ISIN code (unused by this integration).
            conid: IBKR contract ID. Must be a non-empty digit string; returns ``""`` otherwise.

        Returns:
            A fully qualified URL string, or ``""`` if conid is absent/invalid or the icon
            does not exist on the Benzinga proxy.
        """
        if not conid or not conid.isdigit():
            return ""

        icon_type = "mark_dark" if theme.lower() == "dark" else "mark_light"
        query = urlencode(
            {
                "conid": conid,
                "type": icon_type,
                "composite_radius": 0,
                "scale": "200x200",
                "composite_auto": "false",
            }
        )
        url = f"{self.BASE_URL}?{query}"

        try:
            response = requests.get(url, timeout=3, stream=True)
            response.close()
            status_code = getattr(response, "status_code", None)
            if isinstance(status_code, int):
                if status_code >= 400:
                    self.logger.debug(f"No Benzinga icon for conid {conid} (HTTP {status_code})")
                    return ""
            else:
                ok = getattr(response, "ok", None)
                if ok is False:
                    self.logger.debug(f"No Benzinga icon for conid {conid} (HTTP unknown)")
                    return ""
        except RequestException as e:
            self.logger.debug(f"Benzinga request failed for conid {conid}: {e}")
            return ""

        return url
