from datetime import date

from dateutil.relativedelta import relativedelta
from degiro_connector.quotecast.models.chart import Interval

from degiro.utils.localization import LocalizationUtility


def calculate_interval(date_from) -> Interval:
    """Calculate the interval between the provided date and today.

    ### Parameters
        date_from: date from to calculate the interval
    ### Returns
        Interval: Interval that representes the range from date_from to today.
    """
    # Convert String to date object
    d1 = LocalizationUtility.convert_string_to_date(date_from)
    today = date.today()
    # difference between dates in timedelta
    delta = (today - d1).days

    interval = None
    match delta:
        case diff if diff in range(1, 7):
            interval = Interval.P1W
        case diff if diff in range(7, 30):
            interval = Interval.P1M
        case diff if diff in range(30, 90):
            interval = Interval.P3M
        case diff if diff in range(90, 180):
            interval = Interval.P6M
        case diff if diff in range(180, 365):
            interval = Interval.P1Y
        case diff if diff in range(365, 3 * 365):
            interval = Interval.P3Y
        case diff if diff in range(3 * 365, 5 * 365):
            interval = Interval.P5Y
        case diff if diff in range(5 * 365, 10 * 365):
            interval = Interval.P10Y

    return interval

def calculate_dates_in_interval(from_date: date, interval: Interval) -> list:
    # Convert values to dates
    days = convert_interval_to_days(interval)
    start_date = from_date - relativedelta(days=days)
    result = []
    for i in range(1, days):
        day = start_date + relativedelta(days=i)
        result.append(day)

    return result

def convert_interval_to_days(interval: Interval) -> int:
    """Convert and interval into the number of days.

    ### Parameters
        interval: Interval
    ### Returns
        int: Number of days in the interval.
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
