import json
from typing import List

from stonks_overwatch.services.brokers.yfinance.repositories.models import YFinanceStockSplits, YFinanceTickerInfo
from stonks_overwatch.utils.database.db_utils import dictfetchone, get_connection_for_model


class YFinanceRepository:
    @staticmethod
    def get_ticker_info(symbol: str) -> dict | None:
        connection = get_connection_for_model(YFinanceTickerInfo)
        with connection.cursor() as cursor:
            # In case the date is the same, use the id to provide a consistent sorting
            # Use parameterized query to prevent SQL injection
            cursor.execute(
                """
                SELECT data
                FROM yfinance_ticker_info
                WHERE symbol = %s
                """,
                [symbol],
            )
            results = dictfetchone(cursor)

        if results:
            return json.loads(results["data"])

        return None

    @staticmethod
    def get_stock_splits(symbol: str) -> List[dict] | None:
        connection = get_connection_for_model(YFinanceStockSplits)
        with connection.cursor() as cursor:
            # Use parameterized query to prevent SQL injection
            cursor.execute(
                """
                SELECT data
                FROM yfinance_stock_splits
                WHERE symbol = %s
                """,
                [symbol],
            )
            results = dictfetchone(cursor)

        if results:
            return json.loads(results["data"])

        return None
