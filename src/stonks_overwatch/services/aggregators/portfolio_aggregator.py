from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import (
    PortfolioService as BitvavoPortfolioService,
)
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import (
    PortfolioService as DeGiroPortfolioService,
)
from stonks_overwatch.services.brokers.yfinance.services.market_data_service import YFinance
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, PortfolioId, TotalPortfolio
from stonks_overwatch.utils.constants import ProductType, Sector
from stonks_overwatch.utils.logger import StonksLogger

class PortfolioAggregatorService:
    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data", "[AGGREGATOR]")

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_portfolio = DeGiroPortfolioService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_portfolio = BitvavoPortfolioService()
        self.yfinance = YFinance()

    def get_portfolio(self, selected_portfolio: PortfolioId) -> List[PortfolioEntry]:
        self.logger.debug("Get Portfolio")

        portfolio = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            portfolio += self.degiro_portfolio.get_portfolio

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            portfolio += self.bitvavo_portfolio.get_portfolio()

        portfolio = self.__merge_portfolios(portfolio)

        portfolio_total_value = sum([entry.value for entry in portfolio])

        # Calculate Stock Portfolio Size & add missing information
        for entry in portfolio:
            size = entry.value / portfolio_total_value
            entry.portfolio_size = size
            # If some data is missing, we try to get it from yfinance
            if not entry.country and entry.product_type in [ProductType.STOCK, ProductType.ETF]:
                entry.country = self.yfinance.get_country(entry.symbol)

            if ((entry.sector == Sector.UNKNOWN or entry.industry == 'Unknown')
                    and entry.product_type in [ProductType.STOCK]):
                sector, industry = self.yfinance.get_sector_industry(entry.symbol)
                if entry.sector == Sector.UNKNOWN:
                    entry.sector = sector
                if entry.industry == 'Unknown':
                    entry.industry = industry

        return sorted(portfolio, key=lambda k: k.symbol)

    def get_portfolio_total(self, selected_portfolio: PortfolioId) -> TotalPortfolio:
        self.logger.debug("Get Portfolio Total")

        base_currency = Config.default().base_currency

        total_profit_loss = 0.0
        total_cash = 0.0
        portfolio_total_value = 0.0
        total_deposit_withdrawal = 0.0

        if Config.default().is_degiro_enabled(selected_portfolio):
            degiro = self.degiro_portfolio.get_portfolio_total()
            total_profit_loss += degiro.total_pl
            total_cash += degiro.total_cash
            portfolio_total_value += degiro.current_value
            total_deposit_withdrawal += degiro.total_deposit_withdrawal

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            bitvavo = self.bitvavo_portfolio.get_portfolio_total()
            total_profit_loss += bitvavo.total_pl
            total_cash += bitvavo.total_cash
            portfolio_total_value += bitvavo.current_value
            total_deposit_withdrawal += bitvavo.total_deposit_withdrawal

        roi = (portfolio_total_value / total_deposit_withdrawal - 1) * 100

        return TotalPortfolio(
            base_currency=base_currency,
            total_pl=total_profit_loss,
            total_cash=total_cash,
            current_value=portfolio_total_value,
            total_roi=roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )

    @staticmethod
    def __merge_historical_values(historical_values: List[DailyValue]) -> List[DailyValue]:
        merged = {}
        for entry in historical_values:
            date = entry["x"]
            value = entry["y"]
            if date not in merged:
                merged[date] = 0.0
            merged[date] += float(value)

        # FIXME: We can avoid this double conversion by modifying the integration results
        merged = [DailyValue(x=date, y=value) for date, value in sorted(merged.items())]

        return merged

    def calculate_historical_value(self, selected_portfolio: PortfolioId) -> List[DailyValue]:
        self.logger.debug(f"Calculating historical value for {selected_portfolio}")
        historical_value = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            historical_value += self.degiro_portfolio.calculate_historical_value()

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            historical_value += self.bitvavo_portfolio.calculate_historical_value()

        return self.__merge_historical_values(historical_value)


    @staticmethod
    def __merge_portfolios(portfolio_entries: List[PortfolioEntry]) -> List[PortfolioEntry]:
        merged = {}
        for entry in portfolio_entries:
            symbol = entry.symbol
            if symbol not in merged:
                merged[symbol] = entry
            else:
                if entry.product_type == ProductType.CASH:
                    merged[symbol].value += entry.value
                    merged[symbol].base_currency_value += entry.base_currency_value
                else:
                    merged[symbol] = PortfolioAggregatorService.__merge_portfolio_entries(merged[symbol], entry)

        return list(merged.values())

    @staticmethod
    def __merge_portfolio_entries(entry1: PortfolioEntry, entry2: PortfolioEntry) -> PortfolioEntry:
        if entry1.symbol != entry2.symbol:
            raise ValueError("Cannot merge entries with different symbols")

        merged_entry = PortfolioEntry(
            name=entry1.name,
            symbol=entry1.symbol,
            sector=entry1.sector if entry1.sector else entry2.sector,
            industry=entry1.industry if entry1.industry else entry2.industry,
            category=entry1.category if entry1.category else entry2.category,
            exchange=entry1.exchange,
            country=entry1.country,
            product_type=entry1.product_type,
            shares=entry1.shares + entry2.shares,
            product_currency=entry1.product_currency,
            price=entry1.price,
            base_currency_price=entry1.base_currency_price,
            base_currency=entry1.base_currency,
            value=entry1.value + entry2.value,
            base_currency_value=entry1.base_currency_value + entry2.base_currency_value,
            is_open=entry1.is_open,
            unrealized_gain=entry1.unrealized_gain + entry2.unrealized_gain,
            realized_gain=entry1.realized_gain + entry2.realized_gain,
        )

        if entry1.is_open and not entry2.is_open:
            merged_entry.is_open = True
            merged_entry.break_even_price = entry1.break_even_price
            merged_entry.base_currency_break_even_price = entry1.base_currency_break_even_price
        elif not entry1.is_open and entry2.is_open:
            merged_entry.is_open = True
            merged_entry.break_even_price = entry2.break_even_price
            merged_entry.base_currency_break_even_price = entry2.base_currency_break_even_price

        return merged_entry
