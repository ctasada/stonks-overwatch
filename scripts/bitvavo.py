"""poetry run python ./scripts/bitvavo.py"""

import json
import time
from datetime import datetime
from pprint import pprint

from stonks_overwatch.services.bitvavo.bitvavo_service import BitvavoService


# Use this class to connect to Bitvavo and make your first calls.
# Add trading strategies to implement your business logic.
class BitvavoImplementation:
    bitvavo = None
    bitvavo_socket = None

    # Connect securely to Bitvavo, create the WebSocket and error callbacks.
    def __init__(self):
        self.bitvavo = BitvavoService()
        # self.bitvavo_socket = self.bitvavo.newWebsocket()
        # self.bitvavo_socket.setErrorCallback(self.error_callback)

    # Handle errors.
    def error_callback(self, error):
        print("Add your error message.")
        #print("Errors:", json.dumps(error, indent=2))

    def account(self):
        response = self.bitvavo.account()
        print("Account:", json.dumps(response, indent=2))

    def assets(self):
        response = self.bitvavo.assets()
        print("Assets:", json.dumps(response, indent=2))

    def balance(self):
        response = self.bitvavo.balance("EUR")
        print("Balance:", json.dumps(response, indent=2))

    def account_history(self):
        response = self.bitvavo.account_history()
        print("Account History:", json.dumps(response, indent=2))

    def orders(self):
        response = self.bitvavo.get_client().getOrders('ETH-EUR', {})
        print("Orders:", json.dumps(response, indent=2))

    def deposit_history(self):
        response = self.bitvavo.get_client().depositHistory()
        print("Deposit History:", json.dumps(response, indent=2))

    def withdrawal_history(self):
        response = self.bitvavo.get_client().withdrawalHistory()
        print("Withdrawal History:", json.dumps(response, indent=2))

    def ticker_price(self):
        response = self.bitvavo.ticker_price('SOL-EUR')
        print("Ticker Price:", json.dumps(response, indent=2))

    def candles(self):
        start = datetime.fromisoformat('2025-02-08')
        response = self.bitvavo.candles('BTC-EUR', '1d', start)
        pprint(response)

    # Sockets are fast, but asynchronous. Keep the socket open while you are
    # trading.
    def wait_and_close(self):
        # Bitvavo uses a weight based rate limiting system. Your app is limited to 1000 weight points per IP or
        # API key per minute. The rate weighting for each endpoint is supplied in Bitvavo API documentation.
        # This call returns the amount of points left. If you make more requests than permitted by the weight limit,
        # your IP or API key is banned.
        limit = self.bitvavo.get_remaining_limit()
        try:
            while limit > 0:
                time.sleep(0.5)
                limit = self.bitvavo.get_remaining_limit()
        except KeyboardInterrupt:
            self.bitvavo_socket.closeSocket()


# Shall I re-explain main? Naaaaaaaaaa.
if __name__ == '__main__':
    bvavo = BitvavoImplementation()

    # portfolio = PortfolioService()
    # portfolio.get_portfolio()
    # bvavo.account()
    # bvavo.assets()
    # bvavo.balance()
    # bvavo.orders()
    # bvavo.account_history()
    # bvavo.deposit_history()
    # bvavo.withdrawal_history()
    # bvavo.ticker_price()
    bvavo.candles()

    # bvavo.wait_and_close()
