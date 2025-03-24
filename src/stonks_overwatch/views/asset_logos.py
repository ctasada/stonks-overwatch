import requests
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from requests.exceptions import RequestException

from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger

@method_decorator(cache_page(60 * 60), name='get')  # Cache for 1 hour
class AssetLogoView(View):
    logger = StonksLogger.get_logger("stocks_portfolio.dashboard.views", "[VIEW|ASSET_LOGO]")

    # Keep track of alternatives as NVSTly
    # return f"https://raw.githubusercontent.com/nvstly/icons/main/ticker_icons/{symbol.upper()}.png"
    # https://img.stockanalysis.com/logos1/MC/IBE.png
    base_urls = {
        ProductType.STOCK: "https://logos.stockanalysis.com/{}.svg",
        ProductType.ETF: "https://logos.stockanalysis.com/{}.svg",
        ProductType.CRYPTO: "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{}.svg",
    }

    def get(self, request, product_type: str, symbol: str):
        self.logger.debug(f"Fetching logo for {product_type} {symbol}")
        product_type = ProductType.from_str(product_type)
        if product_type == ProductType.UNKNOWN:
            return HttpResponseNotFound("Invalid product type")

        try:
            if product_type == ProductType.CASH:
                return HttpResponse(
                    content=self.__generate_symbol(LocalizationUtility.get_currency_symbol(symbol)),
                    content_type="image/svg+xml",
                    status=200
                )

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
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
                      font-size="{font_size}" font-family="Poppins, sans-serif">{symbol}</text>
            </svg>
            """
