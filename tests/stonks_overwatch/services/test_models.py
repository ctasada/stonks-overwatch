from datetime import datetime

from stonks_overwatch.services.models import (
    AccountOverview,
    Country,
    Deposit,
    DepositType,
    PortfolioEntry,
    PortfolioId,
    TotalPortfolio,
    dataclass_to_dict,
)
from stonks_overwatch.utils.constants import ProductType, Sector

import pytest

def test_portfolio_ids():
    assert PortfolioId.values() == [PortfolioId.ALL, PortfolioId.DEGIRO, PortfolioId.BITVAVO]

    for portfolio_id in PortfolioId.values():
        assert PortfolioId.from_id(portfolio_id.id) == portfolio_id
        as_dict = portfolio_id.to_dict()
        assert as_dict["id"] == portfolio_id.id
        assert as_dict["name"] == portfolio_id.long_name
        assert as_dict["logo"] == portfolio_id.logo

    assert PortfolioId.from_id("XXX") == PortfolioId.ALL

def test_default_account_overview():
    model = AccountOverview()

    with pytest.raises(AttributeError):
        model.date()
    with pytest.raises(AttributeError):
        model.time()
    with pytest.raises(AttributeError):
        model.value_date()
    with pytest.raises(AttributeError):
        model.value_time()
    with pytest.raises(TypeError):
        model.symbol_url()

    assert model.type_str() == ""
    assert model.formated_change() == ""

def test_account_overview():
    now = datetime.now()
    model = AccountOverview(
        datetime=now,
        value_datetime=now,
        stock_name="Apple Inc",
        stock_symbol="AAPL",
        description="Bought some stocks",
        type="BUY_TRANSACTION",
        currency="EUR",
        change=-14.36
    )

    assert model.date() == now.strftime("%Y-%m-%d")
    assert model.time() == now.strftime("%H:%M:%S")
    assert model.value_date() == now.strftime("%Y-%m-%d")
    assert model.value_time() == now.strftime("%H:%M:%S")
    assert model.type_str() == "Buy Transaction"
    assert model.formated_change() == "€ -14.36"
    assert model.symbol_url == "https://logos.stockanalysis.com/aapl.svg"

    model.change = 0
    assert model.formated_change() == ""

def test_country_by_iso_code():
    country = Country("NL")
    assert country.iso_code == "NL"
    assert country.get_name() == "Netherlands"
    assert country.get_flag() == "🇳🇱"

def test_country_by_name():
    country = Country("Netherlands")
    assert country.iso_code == "NL"
    assert country.get_name() == "Netherlands"
    assert country.get_flag() == "🇳🇱"

def test_default_portfolio_entry():
    model = PortfolioEntry()

    assert model.percentage_unrealized_gain == 0.0
    assert model.percentage_realized_gain == 0.0
    with pytest.raises(TypeError):
        model.symbol_url()
    assert model.formatted_portfolio_size() == "0.00%"
    with pytest.raises(ValueError):
        model.formatted_break_even_price()
    with pytest.raises(ValueError):
        model.formatted_base_currency_break_even_price()
    with pytest.raises(ValueError):
        model.formatted_price()
    with pytest.raises(ValueError):
        model.formatted_base_currency_price()
    with pytest.raises(ValueError):
        model.formatted_value()
    with pytest.raises(ValueError):
        model.formatted_base_currency_value()
    with pytest.raises(ValueError):
        model.formatted_unrealized_gain()
    with pytest.raises(ValueError):
        model.formatted_realized_gain()
    assert model.formatted_percentage_unrealized_gain() == "0.00%"
    assert model.formatted_percentage_realized_gain() == "0.00%"

    with pytest.raises(AttributeError):
        model.to_dict()

def test_portfolio_entry():
    model = PortfolioEntry(
        name="Apple Inc",
        symbol="AAPL",
        sector=Sector.TECHNOLOGY,
        industry="Tech",
        category="A",
        exchange_id="NASDAQ",
        exchange_abbr="NASDAQ",
        exchange_name="NASDAQ",
        country=Country("US"),
        product_type=ProductType.STOCK,
        shares=100,
        product_currency="USD",
        price=130.0,
        base_currency_price=119.24,
        base_currency="EUR",
        break_even_price=120.0,
        value=13000.0,
        base_currency_value=11900.0,
        base_currency_break_even_price=100.0,
        is_open=True,
        unrealized_gain=1000.0,
        realized_gain=0.0,
        total_costs=6000.0,
        portfolio_size=0.01,
    )

    assert model.percentage_unrealized_gain == 0.08333333333333333
    assert model.percentage_realized_gain == 0.0
    assert model.symbol_url == "https://logos.stockanalysis.com/aapl.svg"
    assert model.formatted_portfolio_size() == "1.00%"
    assert model.formatted_break_even_price() == "$ 120.00"
    assert model.formatted_base_currency_break_even_price() == "€ 100.00"
    assert model.formatted_price() == "$ 130.00"
    assert model.formatted_base_currency_price() == "€ 119.24"
    assert model.formatted_value() == "$ 13,000.00"
    assert model.formatted_base_currency_value() == "€ 11,900.00"
    assert model.formatted_unrealized_gain() == "€ 1,000.00"
    assert model.formatted_realized_gain() == "€ 0.00"
    assert model.formatted_percentage_unrealized_gain() == "8.33%"
    assert model.formatted_percentage_realized_gain() == "0.00%"

    as_dict = model.to_dict()
    assert as_dict["name"] == "Apple Inc"
    assert as_dict["symbol"] == "AAPL"
    assert as_dict["sector"] == "Technology"
    assert as_dict["industry"] == "Tech"
    assert as_dict["category"] == "A"
    assert as_dict["exchange_id"] == "NASDAQ"
    assert as_dict["symbol_url"] == "https://logos.stockanalysis.com/aapl.svg"


def test_cash_portfolio_entry():
    model = PortfolioEntry(
        name="Cash Balance EUR",
        symbol="EUR",
        product_type=ProductType.CASH,
        product_currency="EUR",
        is_open=True,
        value=100.0,
        base_currency="EUR",
        base_currency_value=100.0
    )

    as_dict = model.to_dict()
    assert as_dict["name"] == "Cash Balance EUR"
    assert as_dict["symbol"] == "EUR"
    assert as_dict["sector"] == ""
    assert as_dict["industry"] == ""
    assert as_dict["category"] == ""
    assert as_dict["exchange_abbr"] == ""

def test_deposit():
    model = Deposit(
        datetime=datetime.fromisoformat("2024-09-16T18:46:52"),
        type=DepositType.DEPOSIT,
        change=100.0,
        currency="EUR",
        description="Deposit for investing",
    )

    assert model.datetime_as_date() == "2024-09-16"
    assert model.change_formatted() == "€ 100.00"

def test_dataclass_to_dict():
    model = TotalPortfolio(
        base_currency="EUR",
        total_pl=1000.0,
        total_cash=50.0,
        current_value=10000.0,
        total_roi=10.0,
        total_deposit_withdrawal=9000.0,
    )

    as_dict = dataclass_to_dict(model)
    assert as_dict['total_pl_formatted'] == "€ 1,000.00"
    assert as_dict['total_cash_formatted'] == "€ 50.00"
    assert as_dict['current_value_formatted'] == "€ 10,000.00"
    assert as_dict['total_roi_formatted'] == "10.00%"
    assert as_dict['total_deposit_withdrawal_formatted'] == "€ 9,000.00"

def test_dataclass_to_dict_exception():
    with pytest.raises(ValueError):
        dataclass_to_dict("string")
