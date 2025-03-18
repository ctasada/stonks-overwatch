from stonks_overwatch.utils.constants import ProductType

def symbol_url(symbol: str, product_type: ProductType) -> str:
    if product_type == ProductType.CRYPTO:
        return f"https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{symbol.lower()}.svg"
    else:
        # Keep track of alternatives as NVSTly
        # return f"https://raw.githubusercontent.com/nvstly/icons/main/ticker_icons/{symbol.upper()}.png"
        # https://img.stockanalysis.com/logos1/MC/IBE.png
        return f"https://logos.stockanalysis.com/{symbol.lower()}.svg"
