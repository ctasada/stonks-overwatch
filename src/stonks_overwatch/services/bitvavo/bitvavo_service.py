import json
import logging
from datetime import datetime

from python_bitvavo_api.bitvavo import Bitvavo, createPostfix

from stonks_overwatch.config.bitvavo_config import BitvavoConfig
from stonks_overwatch.utils.singleton import singleton


@singleton
class BitvavoService:
    START_TIMESTAMP = 0

    logger = logging.getLogger("stocks_portfolio.bitvavo_service")
    client: Bitvavo = None

    def __init__(
            self,
    ):
        self.bitvavo_config = BitvavoConfig.default()
        bitvavo_credentials = self.bitvavo_config.credentials

        if bitvavo_credentials and bitvavo_credentials.apikey and bitvavo_credentials.apisecret:
            self.client = Bitvavo({
                'APIKEY': bitvavo_credentials.apikey,
                'APISECRET': bitvavo_credentials.apisecret
            })

    def get_client(self) -> Bitvavo:
        return self.client

    def get_remaining_limit(self) -> int:
        return self.client.getRemainingLimit()

    def account(self) -> json:
        """Returns the current fees for this account."""
        return self.client.account()

    def account_history(self) -> json:
        """Returns the transaction history for this account."""
        options = {"fromDate": self.START_TIMESTAMP}
        postfix = createPostfix(options)
        return self.client.privateRequest('/account/history', postfix, {}, 'GET')

    def assets(self, symbol: str=None) -> json:
        """Returns information on the supported assets."""
        options = {}
        if symbol:
            options["symbol"] = symbol
        return self.client.assets(options)

    def balance(self, symbol: str=None) -> json:
        """Returns the current balance for this account."""
        options = {}
        if symbol:
            options["symbol"] = symbol
        return self.client.balance(options)

    def candles(self, market: str, interval: str, start: datetime, end: datetime=None) -> list[dict]:
        """
        Retrieve the Open, High, Low, Close, Volume (OHLCV) data you use to create candlestick charts for market with
        interval time between each candlestick.
        Candlestick data is always returned in chronological data from newest to oldest. Data is returned when trades
        are made in the interval represented by that candlestick. When no trades occur you see a gap in data flow,
        zero trades are represented by zero candlesticks.
        """
        response = self.client.candles(market, interval, {}, start=start, end=end)
        result = []
        for candle in response:
            result.append({
                "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
            })
        return result

    def deposit_history(self) -> json:
        """Returns the deposit history of the account."""
        return self.client.depositHistory()

    def ticker_price(self, market: str=None) -> json:
        """Retrieve the price of the latest trades on Bitvavo for all markets or a single market."""
        options = {}
        if market:
            options["market"] = market
        return self.client.tickerPrice(options)

    def withdrawal_history(self) -> json:
        """Returns the withdrawal history."""
        return self.client.withdrawalHistory()
