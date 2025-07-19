from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService

import pook


@pook.on
def test_balance():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    pook.get("https://api.bitvavo.com/v2/balance").reply(200).json(
        [
            {
                "symbol": "BTC",
                "available": 0.00318807,
                "inOrder": "0",
            },
            {
                "symbol": "EUR",
                "available": 100.0,
                "inOrder": "0",
            },
        ]
    )
    client = BitvavoService()
    balance = client.balance()

    assert len(balance) == 2


@pook.on
def test_ticker_price():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"
    pook.get("https://api.bitvavo.com/v2/ticker/price").reply(200).json({"market": "BTC-EUR", "price": "75398"})
    client = BitvavoService()
    result = client.ticker_price("BTC-EUR")
    assert result["market"] == "BTC-EUR"
    assert result["price"] == "75398"


@pook.on
def test_assets():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"
    pook.get("https://api.bitvavo.com/v2/assets").reply(200).json(
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "decimals": 8,
            "depositFee": "0",
            "depositConfirmations": 2,
            "depositStatus": "OK",
            "withdrawalFee": "0.000021",
            "withdrawalMinAmount": "0.000021",
            "withdrawalStatus": "OK",
            "networks": ["BTC"],
            "message": "",
        }
    )
    client = BitvavoService()
    result = client.assets("BTC")
    assert result["symbol"] == "BTC"
    assert result["name"] == "Bitcoin"


@pook.on
def test_account_history():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"
    pook.get("https://api.bitvavo.com/v2/account/history").reply(200).json(
        {
            "items": [
                {
                    "transactionId": "be668b96-4ded-4fcf-80a8-3a94a8e06c8c",
                    "executedAt": "2025-02-08T14:26:45.000Z",
                    "type": "buy",
                    "priceCurrency": "EUR",
                    "priceAmount": "93866",
                    "sentCurrency": "EUR",
                    "sentAmount": "299.25137861999997",
                    "receivedCurrency": "BTC",
                    "receivedAmount": "0.00318807",
                    "feesCurrency": "EUR",
                    "feesAmount": "0.7486213800000314",
                    "address": "null",
                },
            ]
        }
    )
    client = BitvavoService()
    result = client.account_history()

    assert len(result) == 1
    assert result[0]["type"] == "buy"
    assert result[0]["priceCurrency"] == "EUR"


@pook.on
def test_deposit_history():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"
    pook.get("https://api.bitvavo.com/v2/depositHistory").reply(200).json(
        [
            {
                "timestamp": 1739024620000,
                "symbol": "EUR",
                "amount": "400",
                "fee": "0",
                "status": "completed",
                "address": "NL42ABNA1234567891",
            },
        ]
    )
    client = BitvavoService()
    result = client.deposit_history()

    assert len(result) == 1
    assert result[0]["symbol"] == "EUR"
    assert result[0]["amount"] == "400"
