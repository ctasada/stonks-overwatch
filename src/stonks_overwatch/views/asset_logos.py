from enum import Enum

import requests
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from requests.exceptions import RequestException

from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


# Should be extending ProductType
class LogoType(Enum):
    STOCK = "Stock"
    ETF = "ETF"
    CASH = "Cash"
    CRYPTO = "Crypto"
    COUNTRY = "Country"
    SECTOR = "Sector"

    UNKNOWN = "Unknown"

    @staticmethod
    def from_str(label: str):
        value = label.lower()
        if value == "stock":
            return LogoType.STOCK
        elif value == "etf":
            return LogoType.ETF
        elif value == "cash":
            return LogoType.CASH
        elif value == "crypto":
            return LogoType.CRYPTO
        elif value == "country":
            return LogoType.COUNTRY
        elif value == "sector":
            return LogoType.SECTOR

        return LogoType.UNKNOWN


@method_decorator(cache_page(60 * 60), name="get")  # Cache for 1 hour
class AssetLogoView(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|ASSET_LOGO]")
    SVG_CONTENT_TYPE = "image/svg+xml"

    # Keep track of alternatives as NVSTly
    # return f"https://raw.githubusercontent.com/nvstly/icons/main/ticker_icons/{symbol.upper()}.png"
    # https://img.stockanalysis.com/logos1/MC/IBE.png
    base_urls = {
        LogoType.STOCK: "https://logos.stockanalysis.com/{}.svg",
        LogoType.ETF: "https://logos.stockanalysis.com/{}.svg",
        LogoType.CRYPTO: "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{}.svg",
    }

    def get(self, request, product_type: str, symbol: str):
        self.logger.debug(f"Fetching logo for {product_type} {symbol}")
        product_type = LogoType.from_str(product_type)
        if product_type == LogoType.UNKNOWN:
            self.logger.warning(f"Invalid Logo request for {product_type.name} {symbol.upper()}")
            return HttpResponseNotFound("Invalid product type")

        try:
            if product_type == LogoType.CASH:
                return HttpResponse(
                    content=self.__generate_symbol(LocalizationUtility.get_currency_symbol(symbol)),
                    content_type=self.SVG_CONTENT_TYPE,
                    status=200,
                )
            elif product_type == LogoType.COUNTRY:
                # For countries, we can either use the enhanced SVG or the regular Twemoji
                # Check if enhanced flag rendering is requested via query parameter
                use_enhanced = request.GET.get("enhanced", "false").lower() == "true"
                if use_enhanced:
                    return HttpResponse(
                        content=self.__generate_enhanced_flag_svg(symbol),
                        content_type=self.SVG_CONTENT_TYPE,
                        status=200,
                    )
                else:
                    url = self.__emoji_to_svg(symbol)
            elif product_type == LogoType.SECTOR:
                url = self.__emoji_to_svg(symbol)
            else:
                url = self.base_urls[product_type].format(symbol.lower())

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

    def __generate_symbol(self, symbol: str) -> str:
        # We need to fit the logo independently of the symbol length
        font_size = int(300 / len(symbol))
        return f"""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
                <text x="150" y="170" dominant-baseline="middle" text-anchor="middle"
                      font-size="{font_size}" font-family="Poppins, sans-serif">{symbol}</text>
            </svg>
            """

    def __emoji_to_svg(self, emoji_char):
        # Convert emoji to its Unicode codepoint
        codepoint = "-".join(f"{ord(c):x}" for c in emoji_char)

        # Twemoji URL for the SVG. See https://github.com/jdecked/twemoji
        return f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/{codepoint}.svg"

    def __generate_enhanced_flag_svg(self, emoji_char: str) -> str:
        """Generate an enhanced SVG for country flags with better circular presentation."""
        # Convert emoji to its Unicode codepoint for Twemoji
        codepoint = "-".join(f"{ord(c):x}" for c in emoji_char)

        try:
            # First, try to fetch the actual SVG content from Twemoji
            twemoji_url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/{codepoint}.svg"
            response = requests.get(twemoji_url, timeout=5)
            response.raise_for_status()

            # Extract the SVG content and embed it properly
            flag_svg_content = response.text

            # Remove the outer SVG wrapper from the flag content to embed it
            import re

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
                          filter="url(#text-shadow)">{emoji_char}</text>
                </svg>
            """
