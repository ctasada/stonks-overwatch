import logging
from datetime import datetime, timedelta
from typing import List, Optional

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest
from django.utils.functional import cached_property

from stonks_overwatch.config.config import Config
from stonks_overwatch.repositories.degiro.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.repositories.degiro.company_profile_repository import CompanyProfileRepository
from stonks_overwatch.repositories.degiro.product_info_repository import ProductInfoRepository
from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository
from stonks_overwatch.repositories.degiro.transactions_repository import TransactionsRepository
from stonks_overwatch.services.degiro.currency_converter_service import CurrencyConverterService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.deposits import DepositsService
from stonks_overwatch.services.models import Country, DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.constants import ProductType, Sector
from stonks_overwatch.utils.datetime import DateTimeUtility
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.y_finance import get_stock_splits


class PortfolioService:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")

    def __init__(
        self,
        degiro_service: DeGiroService,
    ):
        self.degiro_service = degiro_service
        self.currency_service = CurrencyConverterService()
        self.base_currency = Config.default().base_currency
        self.deposits = DepositsService(
            degiro_service=self.degiro_service,
        )
        self.transactions = TransactionsRepository()
        self.product_info = ProductInfoRepository()

    @cached_property
    def get_portfolio(self) -> List[PortfolioEntry]:
        portfolio_products = self.__get_porfolio_products()

        products_ids = [row["productId"] for row in portfolio_products]
        products_info = self.__get_products_info(products_ids=products_ids)

        products_config = self.__get_product_config()

        my_portfolio = []

        tmp_processed_symbols = []

        for tmp in portfolio_products:
            info = products_info[tmp["productId"]]
            # Products may be closed and reopened with a different productId. We need to keep track of the symbols
            # Find other products for the same symbol. Use data from the 'active' product (should be only one) and
            #   update only the values that are "Unknown" (ideally none)
            if info["symbol"] not in tmp_processed_symbols:
                tmp_products = self.product_info.get_products_info_raw_by_symbol([info["symbol"]])
                correlated_products = [p["id"] for p in tmp_products.values()]
            else:
                continue

            tmp_processed_symbols.append(info["symbol"])

            company_profile = CompanyProfileRepository.get_company_profile_raw(info["isin"])
            sector = None
            industry = "Unknown"
            country = "Unknown"
            if company_profile.get("data"):
                sector = company_profile["data"]["sector"]
                industry = company_profile["data"]["industry"]
                country = company_profile["data"]["contacts"]["COUNTRY"]

            total_realized_gains, total_costs = self.__get_product_realized_gains(correlated_products)

            currency = info["currency"]
            price = ProductQuotationsRepository.get_product_price(tmp["productId"])
            if price == 0.0 and "closePrince" in info:
                self.logger.warning(f"No quotation found for product {tmp['productId']}, using closePrice")
                price = info["closePrice"]

            value = tmp["size"] * price
            break_even_price = tmp["breakEvenPrice"]

            is_open = tmp["size"] != 0.0 and tmp["value"] != 0.0
            unrealized_gain = (price - break_even_price) * tmp["size"]

            if currency != self.base_currency:
                base_currency_price = self.currency_service.convert(price, currency, self.base_currency)
                base_currency_value = self.currency_service.convert(value, currency, self.base_currency)
                base_currency_break_even_price = self.currency_service.convert(
                    break_even_price, currency, self.base_currency
                )
                unrealized_gain = (base_currency_price - base_currency_break_even_price) * tmp["size"]
            else:
                base_currency_price = price
                base_currency_value = value
                base_currency_break_even_price = break_even_price

            exchange_id = info["exchangeId"]
            exchange_abbr = exchange_name = None

            if exchanges := products_config.get("exchanges"):
                exchange = next((ex for ex in exchanges if ex["id"] == int(exchange_id)), None)
                if exchange:
                    exchange_abbr = exchange["hiqAbbr"]
                    exchange_name = exchange["name"]

            my_portfolio.append(
                PortfolioEntry(
                    name=info["name"],
                    symbol=info["symbol"],
                    sector=Sector.from_str(sector),
                    industry=industry,
                    category=info["category"],
                    exchange_id=exchange_id,
                    exchange_abbr=exchange_abbr,
                    exchange_name=exchange_name,
                    country=Country(country) if country != "Unknown" else None,
                    product_type=ProductType.from_str(info["productType"]),
                    shares=tmp["size"],
                    product_currency=currency,
                    price=price,
                    base_currency_price=base_currency_price,
                    base_currency=self.base_currency,
                    break_even_price=break_even_price,
                    base_currency_break_even_price=base_currency_break_even_price,
                    value=value,
                    base_currency_value=base_currency_value,
                    is_open=is_open,
                    unrealized_gain=unrealized_gain,
                    realized_gain=total_realized_gains,
                    total_costs=total_costs,
                )
            )

        total_cash = CashMovementsRepository.get_total_cash()
        my_portfolio.append(
            PortfolioEntry(
                name="Cash Balance EUR",
                symbol="EUR",
                product_type=ProductType.CASH,
                product_currency="EUR",
                value=total_cash,
                base_currency_value=total_cash,
                base_currency="EUR",
                is_open=True,
            )
        )

        return sorted(my_portfolio, key=lambda k: k.symbol)

    def __get_product_realized_gains(self, product_ids: list[str]) -> tuple[float, float]:
        data = self.transactions.get_product_transactions(product_ids)

        buys = [t for t in data if t['buysell'] == 'B']
        sells = [t for t in data if t['buysell'] == 'S']

        # Sort transactions by stock_id and transaction_date
        buys.sort(key=lambda x: x['date'])
        sells.sort(key=lambda x: x['date'])

        # FIFO matching logic
        realized_gains = []
        total_costs = sum([abs(b['quantity']) * b['price'] for b in buys])
        total_realized_gains = 0.0
        for sell in sells:
            sell_qty = abs(sell['quantity'])
            sell_price = sell['price']
            gains = 0.0

            # Match sells with existing buys using FIFO
            for buy in buys:
                if sell_qty <= 0:
                    break

                match_qty = min(sell_qty, buy['quantity'])
                gains += match_qty * (sell_price - buy['price'])

                # Update quantities
                buy['quantity'] -= match_qty
                sell_qty -= match_qty

                # Remove fully used buys
                if buy['quantity'] == 0:
                    buys.remove(buy)

            realized_gains.append({
                'sell_date': sell['date'],
                'realized_gain': gains
            })
            total_realized_gains += gains

        return total_realized_gains, total_costs

    def get_portfolio_total(self, portfolio: Optional[list[dict]] = None) -> TotalPortfolio:
        # Calculate current value
        if not portfolio:
            portfolio = self.get_portfolio

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            if entry.is_open:
                portfolio_total_value += entry.base_currency_value

        tmp_total_portfolio["totalDepositWithdrawal"] = CashMovementsRepository.get_total_cash_deposits_raw()
        tmp_total_portfolio["totalCash"] = CashMovementsRepository.get_total_cash()

        # Try to get the data directly from DeGiro, so we get up-to-date values
        realtime_total_portfolio = self.__get_realtime_portfolio_total()
        if realtime_total_portfolio:
            tmp_total_portfolio = realtime_total_portfolio

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

    def __get_realtime_portfolio_total(self) -> dict | None:
        try:
            update = self.degiro_service.get_client().get_update(
                request_list=[
                    UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
                ],
                raw=True,
            )
            tmp_total_portfolio = {}
            for value in update["totalPortfolio"]["value"]:
                if value.get("value") is not None:
                    tmp_total_portfolio[value["name"]] = value["value"]

            return tmp_total_portfolio
        except Exception:
            return None

    def __get_porfolio_products(self) -> list[dict]:
        try:
            update = self.degiro_service.get_client().get_update(
                request_list=[
                    UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
                ],
                raw=True,
            )
            my_portfolio = []
            # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
            for tmp in update["portfolio"]["value"]:
                # Some products have ids like 'FLATEX_EUR' or 'FLATEX_USD'
                if tmp["id"].isnumeric():
                    portfolio = {}
                    for value in tmp["value"]:
                        if value.get("value") is not None:
                            key = value["name"]
                            if key == "id":
                                key = "productId"
                            portfolio[key] = value["value"]

                    my_portfolio.append(portfolio)
            return my_portfolio

        except Exception:
            logging.exception("Cannot connect to DeGiro, getting last known data")
            local_portfolio = TransactionsRepository.get_portfolio_products()
            for entry in local_portfolio:
                entry["value"] = 1.0  # FIXME

            return local_portfolio

    def __get_products_info(self, products_ids: list) -> dict:
        try:
            return self.degiro_service.get_products_info(products_ids)
        except Exception:
            logging.exception("Cannot connect to DeGiro, getting last known data")
            return ProductInfoRepository.get_products_info_raw(products_ids)

    def __get_product_config(self) -> dict:
        try:
            products_config = self.degiro_service.get_client().get_products_config()

            return products_config
        except Exception:
            return {}

    def calculate_product_growth(self) -> dict:
        results = TransactionsRepository.get_products_transactions()

        product_growth = {}
        for entry in results:
            key = entry["productId"]
            product = product_growth.get(key, {})
            carry_total = product.get("carryTotal", 0)

            stock_date = entry["date"].strftime(LocalizationUtility.DATE_FORMAT)
            carry_total += entry["quantity"]

            product["carryTotal"] = carry_total
            if "history" not in product:
                product["history"] = {}
            product["history"][stock_date] = carry_total
            product_growth[key] = product

        # Cleanup 'carry_total' from result
        for key in product_growth.keys():
            del product_growth[key]["carryTotal"]

        return product_growth


    def calculate_historical_value(self) -> List[DailyValue]:
        cash_account = self.deposits.calculate_cash_account_value()
        data = self._create_products_quotation()

        aggregate = {}
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry)
            convert_fx = entry["product"]["currency"] != self.base_currency
            for date_value in position_value_growth:
                if self._is_weekend(date_value):
                    # Skip weekends. Those days there's no activity
                    continue

                aggregate_value = aggregate.get(date_value, 0)

                if convert_fx:
                    currency = entry["product"]["currency"]
                    fx_date = LocalizationUtility.convert_string_to_date(date_value)
                    value = self.currency_service.convert(
                        position_value_growth[date_value], currency, self.base_currency, fx_date
                    )
                    aggregate_value += value
                else:
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

        stock_splits = get_stock_splits(entry["product"]["symbol"])
        if len(stock_splits) > 0:
            stocks_multiplier = 1
            for split_data in reversed(stock_splits):
                stocks_multiplier = stocks_multiplier * split_data.split_ratio
                for date_value in reversed(position_value):
                    if date_value < LocalizationUtility.format_date_from_date(split_data.date):
                        position_value[date_value] = position_value[date_value] * stocks_multiplier

        aggregate = {}
        if entry["quotation"]["quotes"]:
            for date_quote in entry["quotation"]["quotes"]:
                if date_quote in position_value:
                    aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]
        else:
            self.logger.warning(f"No quotes found for '{entry['product']['symbol']}': productId {entry['productId']} ")

        return aggregate

    def _create_products_quotation(self) -> dict:
        """
        Creates product quotations based on portfolio data and product information.
        """
        product_growth = self.calculate_product_growth()
        tradable_products = {}

        for key, data in product_growth.items():
            product = ProductInfoRepository.get_product_info_from_id(key)

            # If the product is NOT tradable, we shouldn't consider it for Growth
            # The 'tradable' attribute identifies old Stocks, like the ones that are
            # renamed for some reason, and it's not good enough to identify stocks
            # that are provided as dividends, for example.
            if "Non tradeable" in product.get("name", ""):
                continue

            data["productId"] = key
            data["product"] = {
                "name": product["name"],
                "isin": product["isin"],
                "symbol": product["symbol"],
                "currency": product["currency"],
                "vwdId": product["vwdId"],
                "vwdIdSecondary": product["vwdIdSecondary"],
            }

            product_history_dates = list(data["history"].keys())
            data["quotation"] = {
                "fromDate": product_history_dates[0],
                "toDate": product_history_dates[-1],
                "interval": DateTimeUtility.calculate_interval(product_history_dates[0]),
                "quotes": ProductQuotationsRepository.get_product_quotations(key),
            }
            tradable_products[key] = data

        return tradable_products

    @staticmethod
    def _is_weekend(date_str: str):
        # Parse the date string into a datetime object
        day = datetime.strptime(date_str, '%Y-%m-%d')
        # Check if the day of the week is Saturday (5) or Sunday (6)
        return day.weekday() >= 5
