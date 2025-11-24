from decimal import Decimal

from stonks_overwatch.services.brokers.bitvavo.repositories.models import (
    BitvavoAssets,
    BitvavoBalance,
    BitvavoTransactions,
)
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.database.db_utils import dictfetchall, dictfetchone, get_connection_for_model


class BalanceRepository:
    logger = StonksLogger.get_logger("stonks_overwatch.bitvavo_service", "[BITVAVO|REPOSITORY]")

    @staticmethod
    def get_balance_raw() -> list[dict]:
        connection = get_connection_for_model(BitvavoBalance)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_balance
                """
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_balance_for_symbol(symbol: str) -> dict | None:
        """Gets the balance for a specific symbol."""
        connection = get_connection_for_model(BitvavoBalance)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_balance
                WHERE symbol = %s
                """,
                [symbol],
            )
            return dictfetchone(cursor)

    @staticmethod
    def get_balance_calculated() -> list[dict]:
        """Gets the balance from the DB, with the calculated value in EUR."""
        connection = get_connection_for_model(BitvavoTransactions)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM bitvavo_transactions
                ORDER BY executed_at
                """
            )
            entries = dictfetchall(cursor)

        if not entries:
            return []

        # Calculate the balance based on the transactions
        balance_dict = {}

        def process_entry(_symbol: str, _amount: Decimal):
            if not _symbol or not _amount:
                return

            if _symbol in balance_dict:
                balance_dict[_symbol] += _amount
            else:
                balance_dict[_symbol] = _amount

        for entry in entries:
            if "receivedCurrency" in entry:
                symbol = entry["receivedCurrency"]
                amount = Decimal(entry.get("receivedAmount") or 0)
                process_entry(symbol, amount)

            if "sentCurrency" in entry:
                symbol = entry["sentCurrency"]
                amount = -Decimal(entry.get("sentAmount") or 0)
                process_entry(symbol, amount)

        # FIXME: Compare with the Balance available, and keep the 'max'
        # This is a poor substitute to the proper fixes in the API.
        # Bitvavo API has, at least, 2 bugs:
        # 1. When an asset is bought using RFQ (Request for Quote), the transaction doesn't appear in the transactions
        #     returned by the API
        # 2. When an asset uses some kind of blocking Staking, the Balance API returns only the available balance, not
        #     the total balance.

        balance_dict = BalanceRepository._merge_with_raw_balance(balance_dict)

        return [{"symbol": symbol, "amount": amount} for symbol, amount in balance_dict.items()]

    @staticmethod
    def _merge_with_raw_balance(balance_dict):
        """Compares calculated balances with raw balances and applies min/max logic, then rounds to asset decimals."""
        raw_balance = BalanceRepository.get_balance_raw()
        raw_balance_dict = {entry["symbol"]: float(entry.get("available") or 0) for entry in raw_balance}

        for symbol, calc_amount in balance_dict.items():
            raw_amount = raw_balance_dict.get(symbol, 0.0)
            if symbol == "EUR":
                balance_dict[symbol] = min(raw_amount, abs(calc_amount))
            else:
                balance_dict[symbol] = max(raw_amount, calc_amount)

        # Round each balance to the correct number of decimals from BitvavoAssets
        for symbol in list(balance_dict.keys()):
            try:
                asset = BitvavoAssets.objects.get(symbol=symbol)
                decimals = asset.decimals or 0
            except BitvavoAssets.DoesNotExist:
                decimals = 8  # Default to 8 decimals if not found
            balance_dict[symbol] = round(balance_dict[symbol], decimals)

        return balance_dict
