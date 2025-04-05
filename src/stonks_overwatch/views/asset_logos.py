from enum import Enum

import requests
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from requests.exceptions import RequestException

from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger

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

@method_decorator(cache_page(60 * 60), name='get')  # Cache for 1 hour
class AssetLogoView(View):
    logger = StonksLogger.get_logger("stocks_portfolio.dashboard.views", "[VIEW|ASSET_LOGO]")

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
                    content_type="image/svg+xml",
                    status=200
                )
            elif product_type in [LogoType.COUNTRY, LogoType.SECTOR]:
                url = self.__emoji_to_svg(symbol)
            else:
                url = self.base_urls[product_type].format(symbol.lower())

            response = requests.get(url, timeout=5)
            response.raise_for_status()

            return HttpResponse(
                content=response.content,
                content_type=response.headers.get('Content-Type', 'image/svg+xml'),
                status=response.status_code
            )
        except RequestException:
            self.logger.warning(f"Logo for {product_type.name} {symbol.upper()} not found. Creating fallback logo.")
            return HttpResponse(
                content=self.__generate_symbol(symbol.upper()),
                content_type="image/svg+xml",
                status=200
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
        codepoint = '-'.join(f"{ord(c):x}" for c in emoji_char)

        # Twemoji URL for the SVG
        return f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/15.1.0/svg/{codepoint}.svg"
