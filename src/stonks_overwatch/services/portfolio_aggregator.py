import logging

from stonks_overwatch.config import Config
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.portfolio import PortfolioService as DeGiroPortfolioService
from stonks_overwatch.utils.localization import LocalizationUtility


class PortfolioAggregatorService:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_portfolio = DeGiroPortfolioService(
            degiro_service=self.degiro_service,
        )

    def get_portfolio(self) -> list[dict]:
        portfolio = []
        if Config.default().is_degiro_enabled():
            portfolio += self.degiro_portfolio.get_portfolio()

        portfolio_total_value = sum([entry["value"] for entry in portfolio])

        # Calculate Stock Portfolio Size
        for entry in portfolio:
            size = entry["value"] / portfolio_total_value
            entry["portfolioSize"] = size
            entry["formattedPortfolioSize"] = f"{size:.2%}"

        # FIXME: We need to merge the Cash balances. Concatenating is not enough
        return portfolio

    def get_portfolio_total(self):
        base_currency = Config.default().base_currency

        total_profit_loss = 0.0
        total_cash = 0.0
        portfolio_total_value = 0.0
        total_deposit_withdrawal = 0.0

        if Config.default().is_degiro_enabled():
            degiro = self.degiro_portfolio.get_portfolio_total()
            total_profit_loss += degiro["total_pl"]
            total_cash += degiro["totalCash"]
            portfolio_total_value += degiro["currentValue"]
            total_deposit_withdrawal += degiro["totalDepositWithdrawal"]

        roi = (portfolio_total_value / total_deposit_withdrawal - 1) * 100

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency=base_currency,
            ),
            "totalCash": total_cash,
            "totalCash_formatted": LocalizationUtility.format_money_value(
                value=total_cash,
                currency=base_currency,
            ),
            "currentValue": portfolio_total_value,
            "currentValue_formatted": LocalizationUtility.format_money_value(
                value=portfolio_total_value, currency=base_currency
            ),
            "totalROI": roi,
            "totalROI_formatted": "{:,.2f}%".format(roi),
            "totalDepositWithdrawal": total_deposit_withdrawal,
            "totalDepositWithdrawal_formatted": LocalizationUtility.format_money_value(
                value=total_deposit_withdrawal,
                currency=base_currency,
            ),
        }

        return total_portfolio

    @staticmethod
    def __merge_historical_values(historical_values: list[dict]) -> list[dict]:
        merged = {}
        for entry in historical_values:
            date = entry["x"]
            value = entry["y"]
            if date not in merged:
                merged[date] = 0.0
            merged[date] += float(value)

        # FIXME: We can avoid this double conversion by modifying the integration results
        merged = [{"x": date, "y": value} for date, value in sorted(merged.items())]

        return merged

    def calculate_historical_value(self) -> list[dict]:
        historical_value = []
        if Config.default().is_degiro_enabled():
            historical_value += self.degiro_portfolio.calculate_historical_value()

        return self.__merge_historical_values(historical_value)
