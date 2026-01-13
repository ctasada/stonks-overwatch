from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.repositories.assets_repository import AssetsRepository
from stonks_overwatch.services.brokers.bitvavo.repositories.balance_repository import BalanceRepository
from stonks_overwatch.services.brokers.bitvavo.repositories.product_quotations_repository import (
    ProductQuotationsRepository,
)
from stonks_overwatch.services.brokers.bitvavo.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService
from stonks_overwatch.services.brokers.bitvavo.services.transaction_service import TransactionsService
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.datetime import DateTimeUtility
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType


class PortfolioService(BaseService, PortfolioServiceInterface):
    @dataclass
    class Quotation:
        from_date: Optional[str]
        to_date: Optional[str]
        interval: Optional[str]
        quotes: Optional[dict]

    @dataclass
    class Balance:
        symbol: str
        available: str
        in_order: str

    @dataclass
    class Symbol:
        symbol: str
        market: str
        base: str
        quotes: Optional[dict]

    @dataclass
    class Product:
        product_id: Optional[str]
        history: Optional[dict]
        quotation: Optional["PortfolioService.Quotation"]

    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data.bitvavo", "[BITVAVO|PORTFOLIO]")

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.bitvavo_service = BitvavoService()
        self.deposits = DepositsService()
        # Use base_currency property from BaseService which handles dependency injection

    @staticmethod
    def __is_currency(symbol: str) -> bool:
        return symbol == "EUR"

    def get_portfolio(self) -> List[PortfolioEntry]:
        self.logger.debug("Get Portfolio")

        bitvavo_portfolio = []

        balance = BalanceRepository.get_balance_calculated()

        for item in balance:
            if item["amount"] == "0" or self.__is_currency(item["symbol"]):
                continue

            price = self._get_ticket_quotation(item["symbol"])
            value = float(item["amount"]) * price
            asset = AssetsRepository.get_asset(item["symbol"])
            break_even_price = self._get_break_even_price(item["symbol"])
            unrealized_gain = (price - break_even_price) * float(item["amount"])

            bitvavo_portfolio.append(
                PortfolioEntry(
                    symbol=item["symbol"],
                    name=asset["name"],
                    shares=item["amount"],
                    product_type=ProductType.CRYPTO,
                    product_currency=self.base_currency,
                    is_open=True,
                    price=price,
                    value=value,
                    base_currency_price=price,
                    base_currency=self.base_currency,
                    base_currency_value=value,
                    unrealized_gain=unrealized_gain,
                )
            )

        for item in balance:
            if not self.__is_currency(item["symbol"]):
                continue

            bitvavo_portfolio.append(
                PortfolioEntry(
                    symbol=item["symbol"],
                    name="Cash Balance EUR",
                    shares=item["amount"],
                    product_type=ProductType.CASH,
                    product_currency=item["symbol"],
                    is_open=True,
                    value=float(item["amount"]),
                    base_currency=self.base_currency,
                    base_currency_value=float(item["amount"]),
                )
            )

        return sorted(bitvavo_portfolio, key=lambda k: k.symbol)

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        self.logger.debug("Get Portfolio Total")

        # Calculate current value
        if not portfolio:
            portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        for entry in portfolio:
            if entry.is_open:
                portfolio_total_value += entry.base_currency_value

        total_deposit_withdrawal = sum(
            float(deposit["receivedAmount"]) for deposit in TransactionsRepository.get_deposits_history_raw()
        )

        total_cash = 0.0
        balance = BalanceRepository.get_balance_for_symbol(self.base_currency)
        if balance:
            total_cash = balance["available"]

        total_cash = float(total_cash)

        # Handle division by zero case when no deposits exist yet
        if total_deposit_withdrawal and total_deposit_withdrawal > 0:
            roi = (portfolio_total_value / total_deposit_withdrawal - 1) * 100
        else:
            roi = 0.0  # No deposits yet, so no ROI to calculate

        total_profit_loss = portfolio_total_value - total_deposit_withdrawal

        return TotalPortfolio(
            base_currency=self.base_currency,
            total_pl=total_profit_loss,
            total_cash=total_cash,
            current_value=portfolio_total_value,
            total_roi=roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )

    def _get_break_even_price(self, symbol: str) -> float:
        transactions_history = TransactionsRepository.get_transactions_raw()

        total_cost = 0.0
        total_quantity = 0.0

        for transaction in transactions_history:
            if transaction["type"] == "deposit":
                continue

            if transaction["receivedCurrency"] != symbol:
                continue

            total_cost += float(transaction.get("sentAmount") or 0.0) + float(transaction.get("feesAmount") or 0.0)
            total_quantity += float(transaction.get("receivedAmount") or 0.0)

        return total_cost / total_quantity if total_quantity > 0 else 0.0

    @staticmethod
    def _get_growth_final_date(date_str: str):
        if date_str == 0:
            return LocalizationUtility.convert_string_to_date(date_str)
        else:
            return datetime.today().date()

    def _calculate_position_growth(self, entry: dict) -> dict:
        product_history_dates = list(entry["history"].keys())

        start_date = LocalizationUtility.convert_string_to_date(product_history_dates[0])
        final_date = self._get_growth_final_date(product_history_dates[-1])

        # Generate a list of dates between start and final date
        dates = [
            (start_date + timedelta(days=i)).strftime(LocalizationUtility.DATE_FORMAT)
            for i in range((final_date - start_date).days + 1)
        ]

        position_value = {}
        for date_change in entry["history"]:
            index = dates.index(date_change)
            for d in dates[index:]:
                position_value[d] = entry["history"][date_change]

        aggregate = {}
        if entry["quotation"]["quotes"]:
            for date_quote in entry["quotation"]["quotes"]:
                if date_quote in position_value:
                    aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]
        else:
            self.logger.warning(f"No quotes found for '{entry['product']['symbol']}': productId {entry['productId']}")

        return aggregate

    def calculate_historical_value(self) -> List[DailyValue]:
        self.logger.debug("Calculating historical value")

        cash_account = self.deposits.calculate_cash_account_value()
        quotations_per_product = self._create_products_quotation()

        aggregate = {}
        for key in quotations_per_product:
            entry = quotations_per_product[key]
            position_value_growth = self._calculate_position_growth(entry)
            for date_value in position_value_growth:
                if self._is_weekend(date_value):
                    # Skip weekends. There's no trading activity on weekends, even when Crypto works 24x7
                    continue

                aggregate_value = aggregate.get(date_value, 0.0)
                aggregate_value += position_value_growth[date_value]

                aggregate[date_value] = aggregate_value

        dataset = []
        for day in aggregate:
            # Merges the portfolio value with the cash value to get the full picture
            cash_value = 0.0
            if day in cash_account:
                cash_value = cash_account[day]
            else:
                cash_value = list(cash_account.values())[-1]

            day_value = aggregate[day] + cash_value
            dataset.append(DailyValue(x=day, y=LocalizationUtility.round_value(day_value)))

        return dataset

    def calculate_product_growth(self) -> dict:
        self.logger.debug("Calculating Product growth")

        transactions = TransactionsRepository.get_transactions_raw()
        transactions = sorted(transactions, key=lambda k: k["executedAt"], reverse=False)
        transactions = [item for item in transactions if item["type"] in ["buy", "sell", "staking"]]

        product_growth = {}
        tmp_carry_total = {}
        for entry in transactions:
            if entry["type"] in ["buy", "staking"]:
                key = entry["receivedCurrency"]
            else:
                key = entry["sentCurrency"]

            product = product_growth.get(key, {})
            carry_total = tmp_carry_total.get(key, 0)

            stock_date = TransactionsService.format_date(entry["executedAt"])
            if entry["type"] in ["buy", "staking"]:
                carry_total += float(entry["receivedAmount"])
            else:
                carry_total -= float(entry["sentAmount"])

            tmp_carry_total[key] = carry_total
            if "history" not in product:
                product["history"] = {}
            product["history"][stock_date] = carry_total
            product_growth[key] = product

        return product_growth

    def _create_products_quotation(self) -> dict:
        """
        Creates product quotations based on portfolio data and product information.
        """
        product_growth = self.calculate_product_growth()
        tradeable_products = {}

        for key, data in product_growth.items():
            data["productId"] = key

            product_history_dates = list(data["history"].keys())

            start_date = LocalizationUtility.convert_string_to_datetime(product_history_dates[0])
            candles = self.bitvavo_service.candles(f"{key}-{self.base_currency}", "1d", start_date)
            # Creates the dictionary with the date as key and the value as the close price
            date_to_value = {
                start_date + timedelta(days=i): candle["close"]
                for i, candle in enumerate(candles)
                if candle["timestamp"] >= start_date
            }
            quotes = {
                LocalizationUtility.format_date_from_date(date): float(value) for date, value in date_to_value.items()
            }

            data["quotation"] = {
                "fromDate": product_history_dates[0],
                "toDate": product_history_dates[-1],
                "interval": DateTimeUtility.calculate_interval(product_history_dates[0]),
                "quotes": quotes,
            }
            tradeable_products[key] = data

        return tradeable_products

    @staticmethod
    def _is_weekend(date_str: str) -> bool:
        # Parse the date string into a datetime object
        day = datetime.strptime(date_str, "%Y-%m-%d")
        # Check if the day of the week is Saturday (5) or Sunday (6)
        return day.weekday() >= 5

    def _get_ticket_quotation(self, symbol: str) -> float:
        try:
            ticker_json = self.bitvavo_service.ticker_price(symbol + "-" + self.base_currency)
            return float(ticker_json["price"])
        except Exception as e:
            self.logger.error(f"Failed to get ticker quotation for {symbol}: {e}")
            # Fallback to price if ticker quotation fails}
            return ProductQuotationsRepository.get_product_price(symbol)
