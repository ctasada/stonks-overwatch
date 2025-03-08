from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.bitvavo.bitvavo_service import BitvavoService
from stonks_overwatch.services.bitvavo.deposits import DepositsService
from stonks_overwatch.services.bitvavo.transactions import TransactionsService
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.datetime import DateTimeUtility
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger


class PortfolioService:
    @dataclass
    class Quotation:
        from_date: Optional[str]
        to_date: Optional[str]
        interval: Optional[str]
        quotes: Optional[dict]

    @dataclass
    class Product:
        product_id: Optional[str]
        history: Optional[dict]
        quotation: Optional['PortfolioService.Quotation']

    logger = StonksLogger.get_logger("stocks_portfolio.portfolio_data.bitvavo", "[BITVAVO|PORTFOLIO]")

    def __init__(
            self,
    ):
        self.bitvavo_service = BitvavoService()
        self.deposits = DepositsService()
        self.base_currency = Config.default().base_currency

    @staticmethod
    def __is_currency(symbol: str) -> bool:
        return symbol == "EUR"

    def get_portfolio(self) -> List[PortfolioEntry]:
        self.logger.debug("Get Portfolio")

        bitvavo_portfolio = []

        balance = self.bitvavo_service.balance()

        for item in balance:
            if item["available"] == "0" or self.__is_currency(item["symbol"]):
                continue

            ticker_json = self.bitvavo_service.ticker_price(item["symbol"] + "-" + self.base_currency)

            price = float(ticker_json["price"])
            value = float(item["available"]) * price
            asset = self.bitvavo_service.assets(item["symbol"])

            product_type = ProductType.CRYPTO
            if item["symbol"] == self.base_currency:
                product_type = ProductType.CASH

            # FIXME
            break_even_price = self._get_break_even_price(item["symbol"])
            unrealized_gain = (price - break_even_price) * float(item["available"])

            bitvavo_portfolio.append(
                PortfolioEntry(
                    symbol=item["symbol"],
                    name=asset["name"],
                    shares=item["available"],
                    product_type=product_type,
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

        return sorted(bitvavo_portfolio, key=lambda k: k.symbol)


    def get_portfolio_total(self, portfolio: Optional[list[dict]] = None) -> TotalPortfolio:
        self.logger.debug("Get Portfolio Total")

        # Calculate current value
        if not portfolio:
            portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            if entry.is_open:
                portfolio_total_value += entry.base_currency_value

        tmp_total_portfolio["totalDepositWithdrawal"] = (
            sum(float(entry["amount"]) for entry in self.bitvavo_service.deposit_history()))

        total_cash = 0.0
        balance = self.bitvavo_service.balance(self.base_currency)
        if balance:
            total_cash = balance[0]["available"]

        tmp_total_portfolio["totalCash"] = float(total_cash)

        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        return TotalPortfolio(
            total_pl=total_profit_loss,
            total_pl_formatted=LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency=self.base_currency,
            ),
            total_cash=tmp_total_portfolio["totalCash"],
            total_cash_formatted=LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currency=self.base_currency,
            ),
            current_value=portfolio_total_value,
            current_value_formatted=LocalizationUtility.format_money_value(
                value=portfolio_total_value, currency=self.base_currency,
            ),
            total_roi=roi,
            total_roi_formatted="{:,.2f}%".format(roi),
            total_deposit_withdrawal=tmp_total_portfolio["totalDepositWithdrawal"],
            total_deposit_withdrawal_formatted=LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalDepositWithdrawal"],
                currency=self.base_currency,
            ),
        )

    @staticmethod
    def _get_logo_url(symbol: str) -> str:
        return f"https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{symbol.lower()}.svg"

    def _get_break_even_price(self, symbol: str) -> float:
        transactions_history = self.bitvavo_service.account_history()

        total_cost = 0.0
        total_quantity = 0.0

        for transaction in transactions_history["items"]:
            if transaction["type"] == "deposit":
                continue

            if transaction["receivedCurrency"] != symbol:
                continue

            total_cost += float(transaction.get("sentAmount", 0.0)) + float(transaction.get("feesAmount", 0.0))
            total_quantity += float(transaction.get("receivedAmount", 0.0))

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
        dates = [(start_date + timedelta(days=i)).strftime(LocalizationUtility.DATE_FORMAT)
                 for i in range((final_date - start_date).days + 1)]

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

        transactions = self.bitvavo_service.account_history()
        transactions = sorted(transactions["items"], key=lambda k: k["executedAt"], reverse=False)
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
                start_date + timedelta(days=i): candle['close']
                for i, candle in enumerate(candles)
                if candle['timestamp'] >= start_date
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
        day = datetime.strptime(date_str, '%Y-%m-%d')
        # Check if the day of the week is Saturday (5) or Sunday (6)
        return day.weekday() >= 5
