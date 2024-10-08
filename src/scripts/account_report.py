import pandas as pd
from django.db import connection

from degiro.repositories.cash_movements_repository import CashMovementsRepository


def calculate_cash_account() -> None:
    # FIXME: the total value seems to be 24 cents larger :/
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT SUM(change)
            FROM degiro_cashmovements
            WHERE currency = 'EUR'
                AND change IS NOT NULL
                AND type IN ('TRANSACTION', 'CASH_TRANSACTION', 'CASH_FUND_TRANSACTION', 'CASH_FUND_NAV_CHANGE')
            """
        )
        total = cursor.fetchone()

    print(f"Calculated Cash Account = {total[0]}")


def calculate_cash_contributions() -> None:
    cash_contributions = CashMovementsRepository.get_cash_deposits_raw()
    df = pd.DataFrame.from_dict(cash_contributions)

    # Remove hours and keep only the day
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # Group by day, adding the values
    df.set_index("date", inplace=True)
    df = df.sort_values(by="date")
    df = df.groupby(df.index)["change"].sum().reset_index()
    # Do the cummulative sum
    df["contributed"] = df["change"].cumsum()


def run():
    calculate_cash_account()
    calculate_cash_contributions()
    # TODO: Calculate Expenses
    # TODO: Calculate Dividends


if __name__ == "__main__":
    run()
