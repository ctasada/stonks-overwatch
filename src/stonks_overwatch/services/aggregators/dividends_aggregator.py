from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.services.account_service import (
    AccountOverviewService as DeGiroAccountOverviewService,
)
from stonks_overwatch.services.brokers.degiro.services.currency_service import (
    CurrencyConverterService as DeGiroCurrencyConverterService,
)
from stonks_overwatch.services.brokers.degiro.services.dividend_service import (
    DividendsService as DeGiroDividendsService,
)
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import (
    PortfolioService as DeGiroPortfolioService,
)
from stonks_overwatch.services.models import Dividend, PortfolioId

class DividendsAggregatorService:

    def __init__(self):
        self.degiro_service = DeGiroService()

        self.account_overview = DeGiroAccountOverviewService()
        self.currency_service = DeGiroCurrencyConverterService()
        self.portfolio_service = DeGiroPortfolioService(self.degiro_service)
        self.degiro_dividends = DeGiroDividendsService(
            account_overview=self.account_overview,
            currency_service=self.currency_service,
            portfolio_service=self.portfolio_service,
            degiro_service=self.degiro_service,
        )

    def get_dividends(self, selected_portfolio: PortfolioId) -> List[Dividend]:
        dividends = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            dividends += self.degiro_dividends.get_dividends()

        return sorted(dividends, key=lambda k: k.payment_date)
