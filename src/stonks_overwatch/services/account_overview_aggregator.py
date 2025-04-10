from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.bitvavo.account_overview import (
    AccountOverviewService as BitvavoAccountOverviewService,
)
from stonks_overwatch.services.degiro.account_overview import (
    AccountOverviewService as DeGiroAccountOverviewService,
)
from stonks_overwatch.services.models import AccountOverview, PortfolioId

class AccountOverviewAggregatorService:

    def __init__(self):
        self.degiro_account_overview = DeGiroAccountOverviewService()
        self.bitvavo_account_overview = BitvavoAccountOverviewService()

    def get_account_overview(self, selected_portfolio: PortfolioId) -> List[AccountOverview]:
        overview = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            overview += self.degiro_account_overview.get_account_overview()

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            overview += self.bitvavo_account_overview.get_account_overview()

        return sorted(overview, key=lambda k: k.datetime, reverse=True)
