EXPORT_COLUMNS_TRANSACTIONS = [
    "Date",
    "Time",
    "ISIN",
    "Value",
    "Shares",
    "Fees",
    "Taxes",
    "Transaction Currency",
    "Exchange Rate",
    "Type",
]

EXPORT_COLUMNS_ACCOUNT = ["Date", "Time", "Value", "Shares", "Fees", "Transaction Currency", "Type"]

CSV_SEPARATOR = ","
CSV_DECIMAL = "."


def convert_date(date):
    year = str(date.year)
    month = str(date.month)
    day = str(date.day)
    return year + "-" + month + "-" + day
