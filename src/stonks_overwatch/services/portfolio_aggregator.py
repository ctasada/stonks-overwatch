import logging
from typing import List

from stonks_overwatch.config import Config
from stonks_overwatch.services.bitvavo.portfolio import PortfolioService as BitvavoPortfolioService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.portfolio import PortfolioService as DeGiroPortfolioService
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.localization import LocalizationUtility


class PortfolioAggregatorService:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_portfolio = DeGiroPortfolioService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_portfolio = BitvavoPortfolioService()

    def get_portfolio(self) -> List[PortfolioEntry]:
        portfolio = []
        if Config.default().is_degiro_enabled():
            portfolio += self.degiro_portfolio.get_portfolio()

        if Config.default().is_bitvavo_enabled():
            portfolio += self.bitvavo_portfolio.get_portfolio()

        portfolio_total_value = sum([entry.value for entry in portfolio])

        # Calculate Stock Portfolio Size
        for entry in portfolio:
            size = entry.value / portfolio_total_value
            entry.portfolio_Size = size
            entry.formatted_portfolio_size = f"{size:.2%}"

        # FIXME: We need to merge the Cash balances. Concatenating is not enough
        return portfolio

    def get_portfolio_total(self) -> TotalPortfolio:
        base_currency = Config.default().base_currency

        total_profit_loss = 0.0
        total_cash = 0.0
        portfolio_total_value = 0.0
        total_deposit_withdrawal = 0.0

        if Config.default().is_degiro_enabled():
            degiro = self.degiro_portfolio.get_portfolio_total()
            total_profit_loss += degiro.total_pl
            total_cash += degiro.total_cash
            portfolio_total_value += degiro.current_value
            total_deposit_withdrawal += degiro.total_deposit_withdrawal

        if Config.default().is_bitvavo_enabled():
            bitvavo = self.bitvavo_portfolio.get_portfolio_total()
            total_profit_loss += bitvavo.total_pl
            total_cash += bitvavo.total_cash
            portfolio_total_value += bitvavo.current_value
            total_deposit_withdrawal += bitvavo.total_deposit_withdrawal

        roi = (portfolio_total_value / total_deposit_withdrawal - 1) * 100

        return TotalPortfolio(
            total_pl=total_profit_loss,
            total_pl_formatted=LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency=base_currency,
            ),
            total_cash=total_cash,
            total_cash_formatted=LocalizationUtility.format_money_value(
                value=total_cash,
                currency=base_currency,
            ),
            current_value=portfolio_total_value,
            current_value_formatted=LocalizationUtility.format_money_value(
                value=portfolio_total_value, currency=base_currency
            ),
            total_roi=roi,
            total_roi_formatted="{:,.2f}%".format(roi),
            total_deposit_withdrawal=total_deposit_withdrawal,
            total_deposit_withdrawal_formatted=LocalizationUtility.format_money_value(
                value=total_deposit_withdrawal,
                currency=base_currency,
            ),
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

    def calculate_historical_value(self) -> List[DailyValue]:
        historical_value = []
        if Config.default().is_degiro_enabled():
            historical_value += self.degiro_portfolio.calculate_historical_value()

        if Config.default().is_bitvavo_enabled():
            historical_value += self.bitvavo_portfolio.calculate_historical_value()

        return self.__merge_historical_values(historical_value)
