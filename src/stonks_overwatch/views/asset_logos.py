import re
from html import escape

import requests
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from requests.exceptions import RequestException

from stonks_overwatch.integrations.logos.types import LogoType
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


@method_decorator(cache_page(60 * 60), name="get")  # Cache for 1 hour
class AssetLogoView(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|ASSET_LOGO]")
    SVG_CONTENT_TYPE = "image/svg+xml"

    # Twemoji CDN base URL. See https://github.com/jdecked/twemoji
    TWEMOJI_CDN_BASE_URL = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg"

    # Keep track of alternatives as NVSTly
    # return f"https://raw.githubusercontent.com/nvstly/icons/main/ticker_icons/{symbol.upper()}.png"
    # https://img.stockanalysis.com/logos1/MC/IBE.png
    base_urls = {
        LogoType.STOCK: "https://logos.stockanalysis.com/{}.svg",
        LogoType.ETF: "https://logos.stockanalysis.com/{}.svg",
        LogoType.CRYPTO: "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{}.svg",
    }

    def _get_active_integrations(self):
        from stonks_overwatch.config.config import Config
        from stonks_overwatch.constants import BrokerName
        from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
        from stonks_overwatch.integrations.logos.logodev import LogoDevIntegration
        from stonks_overwatch.services.brokers.encryption_utils import decrypt_integration_config
        from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository

        active_integrations = []
        cfg = decrypt_integration_config(Config.get_global().get_setting("integration_logodev", {}))
        if isinstance(cfg, dict) and cfg.get("enabled"):
            api_key = cfg.get("api_key", "").strip()
            if api_key:
                active_integrations.append(LogoDevIntegration(api_key))
            else:
                self.logger.warning("Logo.dev is enabled but the API key could not be decrypted; skipping integration.")

        ibkr_config = BrokersConfigurationRepository.get_broker_by_name(BrokerName.IBKR)
        if ibkr_config and ibkr_config.enabled:
            active_integrations.append(IbkrLogoIntegration())

        return active_integrations

    def get(self, request, product_type: str, symbol: str):
        from stonks_overwatch.config.config import Config

        self.logger.debug(f"Fetching logo for {product_type} {symbol}")
        product_type = LogoType.from_str(product_type)
        if product_type == LogoType.UNKNOWN:
            self.logger.warning(f"Invalid Logo request for {product_type.name} {symbol.upper()}")
            return HttpResponseNotFound("Invalid product type")

        theme = Config.get_global().resolved_theme()
        isin = request.GET.get("isin", "").strip()
        conid = request.GET.get("conid", "").strip()
        if conid and not conid.isdigit():
            self.logger.warning(f"Ignoring invalid conid parameter: {conid}")
            conid = ""

        try:
            integration_response = self._try_integration_logo(product_type, symbol, theme, isin, conid)
            if integration_response:
                return integration_response

            inline = self._resolve_inline_logo(request, product_type, symbol)
            if inline:
                return inline

            url = self._resolve_fallback_url(product_type, symbol)
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return HttpResponse(
                content=response.content,
                content_type=response.headers.get("Content-Type", self.SVG_CONTENT_TYPE),
                status=response.status_code,
            )
        except RequestException:
            self.logger.warning(f"Logo for {product_type.name} {symbol.upper()} not found. Creating fallback logo.")
            return HttpResponse(
                content=self.__generate_symbol(symbol.upper()), content_type=self.SVG_CONTENT_TYPE, status=200
            )

    def _try_integration_logo(
        self, product_type: LogoType, symbol: str, theme: str = "light", isin: str = "", conid: str = ""
    ) -> HttpResponseRedirect | None:
        """Try each active integration in order; redirect the browser directly to the CDN URL.

        Integration APIs (e.g. Logo.dev) are designed for hotlinking — requests must come from
        a browser, not a server-side proxy. Returning a redirect lets the browser fetch the image
        directly, which is both required for authentication and consistent with the intended use.

        Each integration validates logo existence internally via ``get_logo_url()`` and returns
        ``""`` when no logo is available, allowing the loop to fall through to the next integration.
        """
        for integration in self._get_active_integrations():
            self.logger.debug(
                f"Trying integration {integration.__class__.__name__} for {product_type.name} {symbol.upper()}"
            )
            if not integration.supports(product_type):
                self.logger.debug(f"{integration.__class__.__name__} does not support {product_type.name}")
                continue
            url = integration.get_logo_url(product_type, symbol, theme, isin, conid)
            if not url:
                self.logger.debug(f"{integration.__class__.__name__} has no logo for {symbol.upper()}, trying next.")
                continue
            self.logger.debug(f"{integration.__class__.__name__} redirecting to: {url}")
            return HttpResponseRedirect(url)
        return None

    def _resolve_inline_logo(self, request, product_type: LogoType, symbol: str) -> HttpResponse | None:
        """Return an inline SVG response for types that don't use an external URL, or None."""
        if product_type == LogoType.CASH:
            return HttpResponse(
                content=self.__generate_symbol(LocalizationUtility.get_currency_symbol(symbol)),
                content_type=self.SVG_CONTENT_TYPE,
                status=200,
            )
        if product_type == LogoType.COUNTRY and request.GET.get("enhanced", "false").lower() == "true":
            return HttpResponse(
                content=self.__generate_enhanced_flag_svg(symbol),
                content_type=self.SVG_CONTENT_TYPE,
                status=200,
            )
        return None

    def _resolve_fallback_url(self, product_type: LogoType, symbol: str) -> str:
        """Return the CDN/base URL to fetch for types that use an external fallback."""
        if product_type in (LogoType.COUNTRY, LogoType.SECTOR):
            return self.__emoji_to_svg(symbol)
        return self.base_urls[product_type].format(symbol.lower())

    def __generate_symbol(self, symbol: str) -> str:
        # We need to fit the logo independently of the symbol length
        font_size = int(300 / len(symbol))
        escaped = escape(symbol)
        return f"""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
                <text x="150" y="170" dominant-baseline="middle" text-anchor="middle"
                      font-size="{font_size}" font-family="Poppins, sans-serif">{escaped}</text>
            </svg>
            """

    def __emoji_to_svg(self, emoji_char):
        # Convert emoji to its Unicode codepoint
        codepoint = "-".join(f"{ord(c):x}" for c in emoji_char)

        # Return Twemoji SVG URL
        return f"{self.TWEMOJI_CDN_BASE_URL}/{codepoint}.svg"

    def __generate_enhanced_flag_svg(self, emoji_char: str) -> str:
        """Generate an enhanced SVG for country flags with better circular presentation."""
        # Convert emoji to its Unicode codepoint for Twemoji
        codepoint = "-".join(f"{ord(c):x}" for c in emoji_char)

        try:
            # First, try to fetch the actual SVG content from Twemoji
            twemoji_url = f"{self.TWEMOJI_CDN_BASE_URL}/{codepoint}.svg"
            response = requests.get(twemoji_url, timeout=5)
            response.raise_for_status()

            # Extract the SVG content and embed it properly
            flag_svg_content = response.text

            # Remove the outer SVG wrapper from the flag content to embed it
            # Extract everything between <svg...> and </svg>
            svg_match = re.search(r"<svg[^>]*>(.*?)</svg>", flag_svg_content, re.DOTALL)
            if svg_match:
                inner_svg_content = svg_match.group(1)
            else:
                inner_svg_content = flag_svg_content

            # Create an enhanced SVG that properly embeds the flag content
            return f"""
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
                    <defs>
                        <clipPath id="circle-clip">
                            <circle cx="150" cy="150" r="140"/>
                        </clipPath>
                        <filter id="flag-shadow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.3"/>
                        </filter>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#f8f9fa;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="border-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#7386D5;stop-opacity:0.8" />
                            <stop offset="100%" style="stop-color:#6D7FCC;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle cx="150" cy="150" r="145" fill="url(#gradient)" stroke="#7386D5" stroke-width="4"/>
                    <g clip-path="url(#circle-clip)" filter="url(#flag-shadow)"
                        transform="translate(50, 50) scale(3.125)">
                        {inner_svg_content}
                    </g>
                    <circle cx="150" cy="150" r="145" fill="none" stroke="url(#border-gradient)" stroke-width="3"/>
                </svg>
            """
        except (RequestException, Exception):
            # Fallback to a simpler enhanced design with just the emoji
            escaped_emoji = escape(emoji_char)
            return f"""
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#f8f9fa;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="border-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#7386D5;stop-opacity:0.8" />
                            <stop offset="100%" style="stop-color:#6D7FCC;stop-opacity:1" />
                        </linearGradient>
                        <filter id="text-shadow">
                            <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.3"/>
                        </filter>
                    </defs>
                    <circle cx="150" cy="150" r="145" fill="url(#gradient)" stroke="url(#border-gradient)"
                        stroke-width="4"/>
                    <text x="150" y="180" dominant-baseline="middle" text-anchor="middle"
                          font-size="120" font-family="Apple Color Emoji, Segoe UI Emoji, sans-serif"
                          filter="url(#text-shadow)">{escaped_emoji}</text>
                </svg>
            """
