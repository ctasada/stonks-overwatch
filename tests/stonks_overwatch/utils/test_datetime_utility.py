from datetime import date, datetime, timedelta

from degiro_connector.quotecast.models.chart import Interval

from stonks_overwatch.utils.core.datetime import DateTimeUtility

import pytest

def test_calculate_interval_valid_dates():
    # Test cases for valid date ranges
    today = date.today()
    test_cases = [
        ((today + timedelta(days=1)).isoformat(), None),
        (today.isoformat(), Interval.P1D),
        ((today - timedelta(days=2)).isoformat(), Interval.P1W),
        ((today - timedelta(days=6)).isoformat(), Interval.P1W),
        ((today - timedelta(days=29)).isoformat(), Interval.P1M),
        ((today - timedelta(days=89)).isoformat(), Interval.P3M),
        ((today - timedelta(days=179)).isoformat(), Interval.P6M),
        ((today - timedelta(days=364)).isoformat(), Interval.P1Y),
        ((today - timedelta(days=2 * 365)).isoformat(), Interval.P3Y),
        ((today - timedelta(days=4 * 365)).isoformat(), Interval.P5Y),
        ((today - timedelta(days=9 * 365)).isoformat(), Interval.P10Y),
    ]

    for date_str, expected_interval in test_cases:
        interval = DateTimeUtility.calculate_interval(date_str)
        assert interval == expected_interval


def test_calculate_interval_future_date():
    # Test case for a future date
    future_date = (date.today() + timedelta(days=1)).isoformat()
    interval = DateTimeUtility.calculate_interval(future_date)
    assert interval is None


def test_calculate_interval_invalid_date():
    # Test case for an invalid date
    invalid_date = "2023-02-30"
    with pytest.raises(ValueError):
        DateTimeUtility.calculate_interval(invalid_date)


def test_calculate_dates_in_interval():
    to_date = date(2023, 4, 1)
    expected_dates = [
        date(2023, 3, 26),
        date(2023, 3, 27),
        date(2023, 3, 28),
        date(2023, 3, 29),
        date(2023, 3, 30),
        date(2023, 3, 31),
        date(2023, 4, 1),
    ]

    dates = DateTimeUtility.calculate_dates_in_interval(to_date, Interval.P1W)
    assert dates == expected_dates

def test_convert_interval_to_days():
    today = datetime.today()
    start_of_year = datetime(today.year, 1, 1)
    ytd_days = (today - start_of_year).days
    test_cases = [
        (Interval.P1W, 7),
        (Interval.P1M, 30),
        (Interval.P3M, 90),
        (Interval.P6M, 180),
        (Interval.P1Y, 365),
        (Interval.P3Y, 3 * 365),
        (Interval.P5Y, 5 * 365),
        (Interval.P10Y, 10 * 365),
        (Interval.P50Y, 50 * 365),
        (Interval.YTD, ytd_days)
    ]

    for interval, expected_days in test_cases:
        days = DateTimeUtility.convert_interval_to_days(interval)
        assert days == expected_days

    with pytest.raises(ValueError):
        DateTimeUtility.convert_interval_to_days("invalid_interval")
