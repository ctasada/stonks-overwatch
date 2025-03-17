from datetime import datetime

from stonks_overwatch.utils.localization import LocalizationUtility

import pytest

def test_get_currency_symbol():
    assert LocalizationUtility.get_currency_symbol("EUR") == "€"
    assert LocalizationUtility.get_currency_symbol("USD") == "$"


def test_round_value():
    assert LocalizationUtility.round_value(1.2345) == 1.234
    assert LocalizationUtility.round_value(1.2455) == 1.246
    assert LocalizationUtility.round_value(1.2359) == 1.236
    assert LocalizationUtility.round_value(1.2) == 1.2
    assert LocalizationUtility.round_value(1.0) == 1.0


def test_format_money_value_without_currency():
    with pytest.raises(ValueError):
        LocalizationUtility.format_money_value(1.0)

def test_format_money_value_with_currency():
    assert LocalizationUtility.format_money_value(value=1.2345, currency="EUR") == "€ 1.23"
    assert LocalizationUtility.format_money_value(value=1.2345, currency="USD") == "$ 1.23"


def test_format_money_value_with_currency_symbol():
    assert LocalizationUtility.format_money_value(value=1.2345, currency_symbol="€") == "€ 1.23"
    assert LocalizationUtility.format_money_value(value=1.2345, currency_symbol="$") == "$ 1.23"


def test_format_money_value_with_currency_and_symbol():
    assert LocalizationUtility.format_money_value(value=1.2345, currency="EUR", currency_symbol="€") == "€ 1.23"
    assert LocalizationUtility.format_money_value(value=1.2345, currency="USD", currency_symbol="€") == "€ 1.23"
    assert LocalizationUtility.format_money_value(value=1.2345, currency="USD", currency_symbol="$") == "$ 1.23"
    assert LocalizationUtility.format_money_value(value=1.2345, currency="EUR", currency_symbol="$") == "$ 1.23"


def test_format_date_time():
    assert LocalizationUtility.format_date_time("2020-01-01") == "2020-01-01 00:00:00"
    assert LocalizationUtility.format_date_time("2020-01-01 10:10:30") == "2020-01-01 10:10:30"
    assert LocalizationUtility.format_date_time("2020-01-01T10:10:30Z") == "2020-01-01 10:10:30"


def test_format_date():
    assert LocalizationUtility.format_date("2020-01-01T10:10:30Z") == "2020-01-01"


def test_format_time():
    assert LocalizationUtility.format_time("2020-01-01T10:10:30Z") == "10:10:30"


def test_format_date_from_date():
    assert LocalizationUtility.format_date_from_date(datetime.fromisoformat("2020-01-01")) == "2020-01-01"
    assert LocalizationUtility.format_date_from_date(datetime.fromisoformat("2020-01-01 10:10:30")) == "2020-01-01"
    assert LocalizationUtility.format_date_from_date(datetime.fromisoformat("2020-01-01T10:10:30Z")) == "2020-01-01"


def format_time_from_date():
    assert LocalizationUtility.format_time_from_date(datetime.fromisoformat("2020-01-01")) == "00:00:00"
    assert LocalizationUtility.format_time_from_date(datetime.fromisoformat("2020-01-01 10:10:30")) == "10:10:30"
    assert LocalizationUtility.format_time_from_date(datetime.fromisoformat("2020-01-01T10:10:30Z")) == "10:10:30"

def format_date_time_from_date():
    assert LocalizationUtility.format_date_time_from_date(datetime.fromisoformat("2020-01-01")) == "2020-01-01 00:00:00"
    assert (LocalizationUtility.format_date_time_from_date(datetime.fromisoformat("2020-01-01 10:10:30"))
            == "2020-01-01 10:10:30")
    assert (LocalizationUtility.format_date_time_from_date(datetime.fromisoformat("2020-01-01T10:10:30Z"))
            == "2020-01-01 10:10:30")

def test_format_date_to_month_year():
    assert LocalizationUtility.format_date_to_month_year("2020-01-01") == "January 2020"

    assert LocalizationUtility.format_date_to_month_year(datetime.fromisoformat("2020-01-01")) == "January 2020"

def test_get_date_day():
    assert LocalizationUtility.get_date_day("2020-01-01") == "01"

    assert LocalizationUtility.get_date_day(datetime.fromisoformat("2020-01-10")) == "10"


def test_format_date_to_month_number():
    assert LocalizationUtility.format_date_to_month_number("2020-01-01") == "01"
    assert LocalizationUtility.format_date_to_month_number("2020-12-01") == "12"

    assert LocalizationUtility.format_date_to_month_number(datetime.fromisoformat("2020-01-01")) == "01"


def test_format_date_to_year():
    assert LocalizationUtility.format_date_to_year("2020-01-01") == "2020"
    assert LocalizationUtility.format_date_to_year("2020-12-31") == "2020"

    assert LocalizationUtility.format_date_to_year(datetime.fromisoformat("2020-01-01")) == "2020"

def test_month_name():
    assert LocalizationUtility.month_name(1) == "January"
    assert LocalizationUtility.month_name('1') == "January"
    assert LocalizationUtility.month_name(12) == "December"
