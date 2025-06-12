from enum import Enum

from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.logger import StonksLogger

class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ALL = "ALL"

    @staticmethod
    def from_str(label: str):
        value = label.lower()
        if value == "open":
            return PositionStatus.OPEN
        elif value == "closed":
            return PositionStatus.CLOSED
        elif value == "all":
            return PositionStatus.ALL

        return None

class Portfolio(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|PORTFOLIO]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.portfolio_aggregator = PortfolioAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        self.logger.debug(f"Selected Portfolio: {selected_portfolio}")

        portfolio = self.portfolio_aggregator.get_portfolio(selected_portfolio)

        status = self.__parse_request_interval(request)

        stocks = [item for item in portfolio if item.product_type == ProductType.STOCK]
        trackers = [item for item in portfolio if item.product_type == ProductType.ETF]
        cash = [item for item in portfolio if item.product_type == ProductType.CASH]
        cryptos = [item for item in portfolio if item.product_type == ProductType.CRYPTO]

        # print([stock.to_dict() for stock in stocks])

        context = {
            "selected_positions": status.value,
            "stocks": [stock.to_dict() for stock in stocks if self.__show_position(stock, status)],
            "show_stocks_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
                "realized_gain": True,
            },
            "trackers": [tracker.to_dict() for tracker in trackers if self.__show_position(tracker, status)],
            "show_trackers_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
                "realized_gain": True,
            },
            "crypto": [crypto.to_dict() for crypto in cryptos if self.__show_position(crypto, status)],
            "show_crypto_columns": {
                "category": False,
                "sector": False,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
                "realized_gain": True,
            },
            "cash": [currency.to_dict() for currency in cash if self.__show_position(currency, status)],
            "show_cash_columns": {
                "category": False,
                "sector": False,
                "shares": False,
                "price": False,
                "unrealized_gain": False,
                "realized_gain": False,
            },
        }

        return render(request, "portfolio.html", context)

    def __parse_request_interval(self, request) -> PositionStatus:
        """Parse interval from request query parameters."""
        positions = request.GET.get("positions", PositionStatus.OPEN.value)
        if PositionStatus.from_str(positions) is None:
            self.logger.warning(f"Invalid visible positions selected: {positions}. Defaulting to 'OPEN'.")
            positions = "open"

        return PositionStatus.from_str(positions)

    @staticmethod
    def __show_position(entry: PortfolioEntry, status: PositionStatus):
        if status == PositionStatus.ALL:
            return True
        elif status == PositionStatus.OPEN:
            return entry.is_open
        elif status == PositionStatus.CLOSED:
            return not entry.is_open

        return False
