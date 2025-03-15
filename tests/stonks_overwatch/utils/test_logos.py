
from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.logos import symbol_url


def test_crypto_symbol():
    assert symbol_url("BTC", ProductType.CRYPTO) == "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/btc.svg"
    assert symbol_url("btc", ProductType.CRYPTO) == "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/btc.svg"

def test_stock_symbol():
    assert symbol_url("AAPL", ProductType.STOCK) == "https://logos.stockanalysis.com/aapl.svg"
    assert symbol_url("aapl", ProductType.STOCK) == "https://logos.stockanalysis.com/aapl.svg"

def test_etf_symbol():
    assert symbol_url("VWRL", ProductType.ETF) == "https://logos.stockanalysis.com/vwrl.svg"
    assert symbol_url("vwrl", ProductType.ETF) == "https://logos.stockanalysis.com/vwrl.svg"
