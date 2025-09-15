from datetime import datetime, time
from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.repositories.dividends_repository import DividendsRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.services.account_service import AccountOverviewService
from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService
from stonks_overwatch.services.models import Dividend, DividendType
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType


class DividendsService(BaseService, DividendServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.dividends_service", "[DEGIRO|DIVIDENDS]")

    # Constants for dividend transaction descriptions
    DIVIDEND_DESCRIPTIONS = ["Dividend", "Dividendbelasting", "Vermogenswinst"]

    def __init__(
        self,
        account_overview: Optional[AccountOverviewService] = None,
        currency_service: Optional[CurrencyConverterService] = None,
        degiro_service: Optional[DeGiroService] = None,
        portfolio_service: Optional[PortfolioService] = None,
        config: Optional[BaseConfig] = None,
    ):
        super().__init__(config)
        # Auto-create dependencies if not provided
        degiro_svc = degiro_service or DeGiroService()
        self.account_overview = account_overview or AccountOverviewService()
        self.currency_service = currency_service or CurrencyConverterService()
        self.degiro_service = degiro_svc
        self.portfolio_service = portfolio_service or PortfolioService(degiro_service=degiro_svc)

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_dividends(self) -> List[Dividend]:
        dividends = self._get_dividends()
        upcoming_dividends = self._get_upcoming_dividends()
        forecasted_dividends = self._get_forecasted_dividends()

        joined_dividends = dividends + upcoming_dividends + forecasted_dividends

        return sorted(joined_dividends, key=lambda k: k.payment_date)

    def _get_dividends(self) -> List[Dividend]:
        overview = self.account_overview.get_account_overview()

        # Group transactions by date and stock symbol to combine dividend and tax
        dividend_groups = {}

        for transaction in overview:
            if transaction.description in self.DIVIDEND_DESCRIPTIONS:
                # Create a key to group by date and stock symbol
                key = (transaction.value_datetime.date(), transaction.stock_symbol)

                transaction_change = transaction.change
                currency = transaction.currency
                payment_date = transaction.datetime.date()

                if currency != self.base_currency:
                    transaction_change = self.currency_service.convert(
                        transaction_change, currency, self.base_currency, payment_date
                    )
                    currency = self.base_currency

                if key not in dividend_groups:
                    dividend_groups[key] = {
                        "payment_date": transaction.value_datetime,
                        "stock_name": transaction.stock_name,
                        "stock_symbol": transaction.stock_symbol,
                        "currency": currency,
                        "amount": 0.0,
                        "taxes": 0.0,
                    }

                if transaction_change > 0:
                    dividend_groups[key]["amount"] += transaction_change
                else:
                    dividend_groups[key]["taxes"] += abs(transaction_change)

        # Convert grouped data to Dividend objects
        dividends = []
        for group_data in dividend_groups.values():
            dividends.append(
                Dividend(
                    dividend_type=DividendType.PAID,
                    payment_date=group_data["payment_date"],
                    stock_name=group_data["stock_name"],
                    stock_symbol=group_data["stock_symbol"],
                    currency=group_data["currency"],
                    amount=group_data["amount"],
                    taxes=group_data["taxes"],
                )
            )

        return dividends

    def _get_upcoming_dividends(self) -> List[Dividend]:
        result = []
        try:
            upcoming_payments = DividendsRepository.get_upcoming_payments()

            # Group payments by date and stock symbol to combine dividend and tax
            dividend_groups = {}

            for payment in upcoming_payments:
                stock_name = payment["product"]
                stock = ProductInfoRepository.get_product_info_from_name(stock_name)
                if not stock:
                    self.logger.warning(f"Stock info not found for {stock_name}. Skipping upcoming dividend.")
                    continue

                stock_symbol = stock["symbol"]
                payment_date = datetime.combine(payment["payDate"], time.min)

                # Create a key to group by date and stock symbol
                key = (payment_date.date(), stock_symbol)

                amount = float(payment["amount"])
                currency = payment["currency"]
                if currency != self.base_currency:
                    amount = self.currency_service.convert(amount, currency, self.base_currency)
                    currency = self.base_currency

                if key not in dividend_groups:
                    dividend_groups[key] = {
                        "payment_date": payment_date,
                        "stock_name": stock_name,
                        "stock_symbol": stock_symbol,
                        "currency": currency,
                        "amount": 0.0,
                        "taxes": 0.0,
                    }

                if amount > 0:
                    dividend_groups[key]["amount"] += amount
                else:
                    dividend_groups[key]["taxes"] += abs(amount)

            # Convert grouped data to Dividend objects
            for group_data in dividend_groups.values():
                result.append(
                    Dividend(
                        dividend_type=DividendType.ANNOUNCED,
                        payment_date=group_data["payment_date"],
                        stock_name=group_data["stock_name"],
                        stock_symbol=group_data["stock_symbol"],
                        currency=group_data["currency"],
                        amount=group_data["amount"],
                        taxes=group_data["taxes"],
                    )
                )

            return result
        except Exception as error:
            self.logger.error(error, exc_info=True)
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

                    currency = forecasted_dividends["currency"]
                    if currency != self.base_currency:
                        amount = self.currency_service.convert(amount, currency, self.base_currency)
                        currency = self.base_currency

                    result.append(
                        Dividend(
                            dividend_type=DividendType.FORECASTED,
                            payment_date=forecasted_dividends["paymentDate"],
                            stock_name=entry.name,
                            stock_symbol=entry.symbol,
                            currency=currency,
                            amount=amount,
                        )
                    )

                    if (
                        forecasted_dividends["exDividendDate"]
                        and forecasted_dividends["exDividendDate"].date() > datetime.now().date()
                    ):
                        result.append(
                            Dividend(
                                dividend_type=DividendType.EX_DIVIDEND,
                                payment_date=forecasted_dividends["exDividendDate"],
                                stock_name=entry.name,
                                stock_symbol=entry.symbol,
                                currency=currency,
                                amount=amount,
                                payout_date=forecasted_dividends["paymentDate"],
                            )
                        )

        return result
