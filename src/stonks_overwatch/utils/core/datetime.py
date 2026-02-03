from datetime import date, timedelta
from typing import Optional

from degiro_connector.quotecast.models.chart import Interval
from django.utils import timezone


class DateTimeUtility:
    """
    A utility class for handling date and time-related operations.
    """

    @staticmethod
    def calculate_interval(date_from: str) -> Optional[Interval]:  # noqa: C901
        """
        Calculate the interval between the provided date and today.

        Args:
            date_from (str): The start date in ISO format (YYYY-MM-DD).

        Returns:
            Optional[Interval]: The interval representing the range from date_from to today.
                                Returns None if the date_from is invalid or in the future.
        """
        d1 = date.fromisoformat(date_from)
        today = timezone.now().date()

        if d1 > today:
            return None

        delta = (today - d1).days

        interval = None
        if delta == 0:
            interval = Interval.P1D
        elif 1 <= delta < 7:
            interval = Interval.P1W
        elif 7 <= delta < 30:
            interval = Interval.P1M
        elif 30 <= delta < 90:
            interval = Interval.P3M
        elif 90 <= delta < 180:
            interval = Interval.P6M
        elif 180 <= delta < 365:
            interval = Interval.P1Y
        elif 365 <= delta < 3 * 365:
            interval = Interval.P3Y
        elif 3 * 365 <= delta < 5 * 365:
            interval = Interval.P5Y
        elif 5 * 365 <= delta < 10 * 365:
            interval = Interval.P10Y

        return interval

    @staticmethod
    def calculate_dates_in_interval(to_date: date, interval: Interval) -> list[date]:
        """
        Calculate the list of dates within the given interval.

        Args:
            to_date (date): The start date.
            interval (Interval): The interval for which to calculate the dates.

        Returns:
            list[date]: A list of dates within the given interval.
        """
        days = DateTimeUtility.convert_interval_to_days(interval)
        start_date = to_date - timedelta(days=days - 1)
        return [start_date + timedelta(days=i) for i in range(0, days)]

    @staticmethod
    def convert_interval_to_days(interval: Interval) -> int:  # noqa: C901
        """
        Convert an interval into the number of days.

        Args:
            interval (Interval): The interval to convert.

        Returns:
            int: The number of days in the interval.
        """
        match interval:
            case Interval.P1W:
                return 7
            case Interval.P1M:
                return 30
            case Interval.P3M:
                return 90
            case Interval.P6M:
                return 180
            case Interval.P1Y:
                return 365
            case Interval.P3Y:
                return 3 * 365
            case Interval.P5Y:
                return 5 * 365
            case Interval.P10Y:
                return 10 * 365
            case Interval.P50Y:
                return 50 * 365
            case Interval.YTD:
                return (timezone.now().date() - date(timezone.now().date().year, 1, 1)).days
            case _:
                raise ValueError(f"Invalid interval: {interval}")
