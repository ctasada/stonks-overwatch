import json
from typing import List

from stonks_overwatch.services.brokers.yfinance.repositories.models import YFinanceStockSplits, YFinanceTickerInfo
from stonks_overwatch.utils.database.db_utils import dictfetchone, get_connection_for_model


class YFinanceRepository:
    @staticmethod
    def _normalize_json_payload(payload: object) -> object:
        """Normalize payload to JSON-serializable primitives."""
        return json.loads(json.dumps(payload, default=str))

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

    @staticmethod
    def save_ticker_info(symbol: str, ticker_info: dict) -> None:
        normalized = YFinanceRepository._normalize_json_payload(ticker_info)
        YFinanceTickerInfo.objects.update_or_create(symbol=symbol, defaults={"data": normalized})

    @staticmethod
    def save_stock_splits(symbol: str, splits: List[dict]) -> None:
        normalized = YFinanceRepository._normalize_json_payload(splits)
        YFinanceStockSplits.objects.update_or_create(symbol=symbol, defaults={"data": normalized})
