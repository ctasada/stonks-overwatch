from datetime import datetime, time
from typing import List

from stonks_overwatch.config.config import Config
from ..repositories.dividends_repository import DividendsRepository
from ..repositories.product_info_repository import ProductInfoRepository
from .account_service import AccountOverviewService
from .currency_service import CurrencyConverterService
from ..client.degiro_client import DeGiroService
from .portfolio_service import PortfolioService
from stonks_overwatch.services.models import Dividend, DividendType
from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.logger import StonksLogger

class DividendsService:
    logger = StonksLogger.get_logger("stonks_overwatch.dividends_service", "[DEGIRO|DIVIDENDS]")

    def __init__(
        self,
        account_overview: AccountOverviewService,
        currency_service: CurrencyConverterService,
        degiro_service: DeGiroService,
        portfolio_service: PortfolioService,
    ):
        self.account_overview = account_overview
        self.currency_service = currency_service
        self.portfolio_service = portfolio_service
        self.degiro_service = degiro_service
        self.base_currency = Config.default().base_currency

    def get_dividends(self) -> List[Dividend]:
        dividends = self._get_dividends()
        upcoming_dividends = self._get_upcoming_dividends()
        forecasted_dividends = self._get_forecasted_dividends()

        joined_dividends = dividends + upcoming_dividends + forecasted_dividends

        return sorted(joined_dividends, key=lambda k: k.payment_date)

    def _get_dividends(self) -> List[Dividend]:
        overview = self.account_overview.get_account_overview()

        dividends = []
        for transaction in overview:
            # We don't include 'Dividendbelasting' because the 'value' seems to already include the taxes
            if transaction.description in [
                "Dividend",
                "Dividendbelasting",
                "Vermogenswinst",
            ]:
                transaction_change = transaction.change
                currency = transaction.currency
                payment_date = transaction.datetime.date()
                if currency != self.base_currency:
                    transaction_change = self.currency_service.convert(
                        transaction_change, currency, self.base_currency, payment_date
                    )
                    currency = self.base_currency

                dividends.append(
                    Dividend(
                        dividend_type = DividendType.PAID,
                        payment_date=transaction.datetime,
                        stock_name=transaction.stock_name,
                        stock_symbol=transaction.stock_symbol,
                        currency=currency,
                        change=transaction_change,
                    )
                )

        return dividends

    def _get_upcoming_dividends(self) -> List[Dividend]:
        result = []
        try:
            upcoming_payments = DividendsRepository.get_upcoming_payments()
            for payment in upcoming_payments:
                stock_name = payment["product"]
                stock = ProductInfoRepository.get_product_info_from_name(stock_name)
                stock_symbol = stock["symbol"]

                amount = float(payment["amount"])
                currency = payment["currency"]
                result.append(
                    Dividend(
                        dividend_type=DividendType.ANNOUNCED,
                        payment_date=datetime.combine(payment["payDate"], time.min),
                        stock_name=stock_name,
                        stock_symbol=stock_symbol,
                        currency=currency,
                        change=amount,
                    )
                )

            return result
        except Exception as error:
            self.logger.error(error)
            return result

    def _get_forecasted_dividends(self) -> List[Dividend]:
        result = []

        portfolio = self.portfolio_service.get_portfolio

        for entry in portfolio:
            if entry.is_open and entry.product_type == ProductType.STOCK:
                forecasted_dividends = DividendsRepository.get_forecasted_payments(isin=entry.isin)

                if forecasted_dividends:
                    amount = float(0.0)
                    if "dividend" in forecasted_dividends and forecasted_dividends["dividend"] is not None:
                        amount = float(forecasted_dividends["dividend"]) * entry.shares
                    else:
                        self.logger.warning(f"No dividend amount found for {entry.name} ({entry.isin})")

                    result.append(
                        Dividend(
                            dividend_type=DividendType.FORECASTED,
                            payment_date=forecasted_dividends["paymentDate"],
                            ex_dividend_date=forecasted_dividends['exDividendDate'],
                            stock_name=entry.name,
                            stock_symbol=entry.symbol,
                            currency=forecasted_dividends['currency'],
                            change=amount,
                        )
                    )

        return result
