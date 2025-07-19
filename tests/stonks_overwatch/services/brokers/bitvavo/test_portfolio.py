from isodate import parse_datetime

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.services.brokers.bitvavo.repositories.models import (
    BitvavoAssets,
    BitvavoBalance,
    BitvavoDepositHistory,
    BitvavoTransactions,
)
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import PortfolioService
from stonks_overwatch.services.models import PortfolioEntry, ProductType

import pook
import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestPortfolioService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_balance_repository()
        self.fixture_transactions_repository()
        self.fixture_assets_repository()
        self.fixture_deposit_history_repository()

    def fixture_balance_repository(self):
        data = [
            {
                "symbol": "BTC",
                "available": 0.00318807,
            },
            {
                "symbol": "EUR",
                "available": 100.0,
            },
        ]

        for value in data:
            # Create and save the CashMovements object
            obj = BitvavoBalance.objects.create(**value)
            self.created_objects[value["symbol"]] = obj

    def fixture_transactions_repository(self):
        data = [
            {
                "transaction_id": "be668b96-4ded-4fcf-80a8-3a94a8e06c8c",
                "executed_at": "2025-02-08T14:26:45.000Z",
                "type": "buy",
                "price_currency": "EUR",
                "price_amount": "93866",
                "sent_currency": "EUR",
                "sent_amount": "299.25137861999997",
                "received_currency": "BTC",
                "received_amount": "0.00318807",
                "fees_currency": "EUR",
                "fees_amount": "0.7486213800000314",
                "address": "null",
            },
        ]

        for value in data:
            value["executed_at"] = parse_datetime(value["executed_at"])

            # Create and save the CashMovements object
            obj = BitvavoTransactions.objects.create(**value)
            self.created_objects[value["transaction_id"]] = obj

    def fixture_assets_repository(self):
        data = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "decimals": 8,
                "deposit_fee": "0",
                "deposit_confirmations": 2,
                "deposit_status": "OK",
                "withdrawal_fee": "0.000021",
                "withdrawal_min_amount": "0.000021",
                "withdrawal_status": "OK",
                "networks": ["BTC"],
                "message": "",
            }
        ]

        for value in data:
            # Create and save the CashMovements object
            obj = BitvavoAssets.objects.create(**value)
            self.created_objects[value["symbol"]] = obj

    def fixture_deposit_history_repository(self):
        data = [
            {
                "timestamp": "2025-02-08T14:26:45.000Z",
                "symbol": "EUR",
                "amount": "400",
                "fee": "0",
                "status": "completed",
                "address": "NL42ABNA1234567891",
            },
        ]

        for value in data:
            value["timestamp"] = parse_datetime(value["timestamp"])
            # Create and save the CashMovements object
            obj = BitvavoDepositHistory.objects.create(**value)
            self.created_objects[value["symbol"]] = obj

    @pook.on
    def test_get_portfolio(self):
        BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

        pook.get("https://api.bitvavo.com/v2/ticker/price").reply(200).json({"market": "BTC-EUR", "price": "75398"})

        portfolio = PortfolioService().get_portfolio()

        assert len(portfolio) == 2
        assert portfolio[0].symbol == "BTC"
        assert portfolio[0].name == "Bitcoin"
        assert portfolio[0].shares == 0.00318807
        assert portfolio[0].product_type == ProductType.CRYPTO
        assert portfolio[0].product_currency == "EUR"
        assert portfolio[0].is_open is True
        assert portfolio[0].price == 75398
        assert portfolio[0].value == 240.37410186
        assert portfolio[0].base_currency_price == 75398
        assert portfolio[0].base_currency == "EUR"
        assert portfolio[0].base_currency_value == 240.37410186
        assert portfolio[0].unrealized_gain == -59.62589814000001

        assert portfolio[1].symbol == "EUR"
        assert portfolio[1].name == "Cash Balance EUR"
        assert portfolio[1].shares == 100.0
        assert portfolio[1].product_type == ProductType.CASH
        assert portfolio[1].product_currency == "EUR"
        assert portfolio[1].is_open is True
        assert portfolio[1].price == 0.0
        assert portfolio[1].value == 100.0
        assert portfolio[1].base_currency_price == 0.0
        assert portfolio[1].base_currency == "EUR"
        assert portfolio[1].base_currency_value == 100.0
        assert portfolio[1].unrealized_gain == 0.0

    @pook.on
    def test_get_portfolio_total(self):
        BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

        portfolio = [
            PortfolioEntry(
                name="Bitcoin",
                symbol="BTC",
                product_type=ProductType.CRYPTO,
                product_currency="EUR",
                is_open=True,
                price=75398,
                value=240.37410186,
                base_currency_price=75398,
                base_currency="EUR",
                base_currency_value=240.37410186,
                unrealized_gain=-59.62589814000001,
            ),
            PortfolioEntry(
                name="Cash Balance EUR",
                symbol="EUR",
                product_type=ProductType.CASH,
                product_currency="EUR",
                is_open=True,
                value=100.0,
                base_currency="EUR",
                base_currency_value=100.0,
            ),
        ]
        total_portfolio = PortfolioService().get_portfolio_total(portfolio)

        assert total_portfolio.total_pl == -59.625898140000004
        assert total_portfolio.total_pl_formatted == "€ -59.63"
        assert total_portfolio.total_cash == 100
        assert total_portfolio.total_cash_formatted == "€ 100.00"
        assert total_portfolio.current_value == 340.37410186
        assert total_portfolio.current_value_formatted == "€ 340.37"
        assert total_portfolio.total_roi == -14.906474535000003
        assert total_portfolio.total_roi_formatted == "-14.91%"
        assert total_portfolio.total_deposit_withdrawal == 400
        assert total_portfolio.total_deposit_withdrawal_formatted == "€ 400.00"
