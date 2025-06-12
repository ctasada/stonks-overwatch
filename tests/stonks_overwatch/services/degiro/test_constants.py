from stonks_overwatch.services.brokers.degiro.client.constants import CurrencyFX, ProductType, TransactionType

import pytest

def test_transaction_type_from_int():
    for t in TransactionType:
        assert TransactionType.from_int(t.value) == t

    assert TransactionType.from_int(999) == TransactionType.UNKNOWN

def test_transaction_type_invalid():
    with pytest.raises(ValueError):
        TransactionType("INVALID_TYPE")

def test_transaction_type_to_str():
    assert TransactionType.BUY_SELL.to_string() == ""
    assert TransactionType.STOCK_SPLIT.to_string() == "Stock Split"
    assert TransactionType.UNKNOWN.to_string() == "Unknown Transaction Type"

def test_product_type_from_int():
    for t in ProductType:
        assert ProductType.from_int(t.value) == t

    assert ProductType.from_int(999) == ProductType.UNKNOWN

def test_product_type_invalid():
    with pytest.raises(ValueError):
        ProductType("INVALID_TYPE")

def test_product_type_to_str():
    assert ProductType.STOCK.to_string() == "Stock"
    assert ProductType.ETF.to_string() == "ETF"
    assert ProductType.CASH.to_string() == "Cash"
    assert ProductType.UNKNOWN.to_string() == "Unknown Product Type"

def test_currency_fx_to_list():
    assert CurrencyFX.to_list() == [705366]

def test_currency_fx_to_str_list():
    assert CurrencyFX.to_str_list() == ['705366']

def test_currency_fx_known_currencies():
    assert CurrencyFX.known_currencies() == ['EUR', 'USD']
