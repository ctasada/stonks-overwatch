import logging
from datetime import datetime, timedelta
from typing import List

from stonks_overwatch.services.bitvavo.bitvavo_service import BitvavoService
from stonks_overwatch.services.bitvavo.transactions import TransactionsService
from stonks_overwatch.services.models import Deposit
from stonks_overwatch.utils.localization import LocalizationUtility


class DepositsService:
    logger = logging.getLogger("stocks_portfolio.deposits.bitvavo")

    def __init__(
            self,
    ):
        self.bitvavo_service = BitvavoService()

    def get_cash_deposits(self) -> List[Deposit]:
        history = []

        deposits = self.bitvavo_service.deposit_history()
        withdrawal = self.bitvavo_service.withdrawal_history()

        for entry in deposits:
            date = datetime.fromtimestamp(entry["timestamp"] / 1000)
            amount = float(entry["amount"])
            history.append(
                Deposit(
                    date=LocalizationUtility.format_date_from_date(date),
                    type="Deposit",
                    change=amount,
                    change_formatted=LocalizationUtility.format_money_value(
                        value=amount, currency=entry["symbol"]
                    ),
                    description="Bitvavo Deposit",
                )
            )

        for entry in withdrawal:
            date = datetime.fromtimestamp(entry["timestamp"] / 1000)
            amount = float(entry["amount"])
            history.append(
                Deposit(
                    date=LocalizationUtility.format_date_from_date(date),
                    type="Withdrawal",
                    change=amount,
                    change_formatted=LocalizationUtility.format_money_value(
                        value=amount, currency=entry["symbol"]
                    ),
                    description="Bitvavo Withdrawal",
                )
            )
        return history

    @staticmethod
    def __fill_missing_dates(data: dict[str, float]) -> dict[str, float]:
        """
        Fill missing dates in the sorted dictionary with the last known value.

        :param data: A sorted dictionary with dates as keys (string in 'YYYY-MM-DD')
                     and values as the associated value.
        :return: A dictionary with all dates filled and the last known value for missing dates.
        """
        # Ensure the dictionary is sorted (just in case)
        sorted_data = dict(sorted(data.items(), key=lambda x: x[0]))

        # Initialize variables
        filled_data = {}
        last_known_value = None

        # Convert string dates to datetime objects for manipulation
        start_date = datetime.fromisoformat(sorted(sorted_data.keys())[0])
        end_date = datetime.today()

        # Iterate over the full date range
        current_date = start_date
        while current_date <= end_date:
            date_str = LocalizationUtility.format_date_from_date(current_date)
            if date_str in sorted_data:
                # Update last known value
                last_known_value = sorted_data[date_str]
                filled_data[date_str] = last_known_value
            else:
                # Fill missing date with the last known value
                filled_data[date_str] = last_known_value
            current_date += timedelta(days=1)

        return filled_data

    def calculate_cash_account_value(self) -> dict[str, float]:
        transactions = self.bitvavo_service.account_history()
        transactions = sorted(transactions["items"], key=lambda k: k["executedAt"], reverse=False)
        transactions = [item for item in transactions if item["type"] in ["deposit", "withdrawal", "buy", "sell"]]

        dataset = {}
        cash_value = 0.0
        for transaction in transactions:
            cash_value -= float(transaction["feesAmount"])
            if transaction["type"] in ["deposit", "sell"]:
                cash_value += float(transaction["receivedAmount"])
            elif transaction["type"] in ["buy", "withdrawal"]:
                cash_value -= float(transaction["sentAmount"])
            else:
                self.logger.error("Unknown transaction type:", transaction["type"])

            dataset[TransactionsService.format_date(transaction["executedAt"])] = round(cash_value, 2)

        return self.__fill_missing_dates(dataset)
