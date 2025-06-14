from datetime import datetime


def assert_dates_descending(data: dict, date_column: str = "date", convert_from_str: bool = False):
    """
    Asserts that the dates in the given dictionary are in descending order.
    """
    sorted_data = sorted(data, key=lambda x: x[date_column], reverse=True)

    prev_date = None
    for entry in sorted_data:
        date = entry[date_column]
        if convert_from_str:
            date = datetime.fromisoformat(entry[date_column])

        if prev_date is not None and date > prev_date:
            raise AssertionError(f"Date {date} is not newer than the previous date {prev_date}")
        prev_date = date
