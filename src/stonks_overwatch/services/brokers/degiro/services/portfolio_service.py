from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest
from django.utils.functional import cached_property
from iso10383 import MIC

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroOfflineModeError, DeGiroService
from stonks_overwatch.services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.brokers.degiro.repositories.company_profile_repository import CompanyProfileRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_quotations_repository import (
    ProductQuotationsRepository,
)
from stonks_overwatch.services.brokers.degiro.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService
from stonks_overwatch.services.brokers.degiro.services.deposit_service import DepositsService
from stonks_overwatch.services.brokers.degiro.services.helper import is_non_tradeable_product
from stonks_overwatch.services.brokers.yfinance.services.market_data_service import YFinance
from stonks_overwatch.services.models import Country, DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.settings import TIME_ZONE
from stonks_overwatch.utils.core.datetime import DateTimeUtility
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType, Sector


class PortfolioService(BaseService, PortfolioServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data.degiro", "[DEGIRO|PORTFOLIO]")

    # Configuration constants
    SUPPORTED_CURRENCY_ACCOUNTS = ["EUR", "USD", "GBP"]
    DEBUG_SYMBOL = "NVDA"  # Change this to debug other symbols
    DEBUG_DATES = ["2021-07-18", "2021-07-19", "2021-07-20"]  # Adjust for specific date ranges

    # Product type constants
    CASH_PRODUCT_TYPE = "CASH"
    NON_TRADEABLE_IDENTIFIER = "Non tradeable"

    # Field name constants
    CLOSE_PRICE_FIELD = "closePrice"
    PRODUCT_ID_FIELD = "productId"

    # Default values
    DEFAULT_PORTFOLIO_VALUE = 1.0
    FALLBACK_PRICE = 0.0

    # Display constants
    CASH_BALANCE_NAME_TEMPLATE = "Cash Balance {currency}"

    def __init__(
        self,
        degiro_service: Optional[DeGiroService] = None,
        config: Optional[BaseConfig] = None,
    ):
        super().__init__(config)
        self.degiro_service = degiro_service or DeGiroService()
        self.currency_service = CurrencyConverterService()
        # Use base_currency property from BaseService which handles dependency injection
        self.deposits = DepositsService(
            degiro_service=self.degiro_service,
        )
        self.transactions = TransactionsRepository()
        self.product_info = ProductInfoRepository()
        self.yfinance = YFinance()

    @cached_property
    def get_portfolio(self) -> List[PortfolioEntry]:
        self.logger.debug("Get Portfolio")

        portfolio_products = self.__get_portfolio_products()
        products_ids = [row[self.PRODUCT_ID_FIELD] for row in portfolio_products]
        products_info = self.__get_products_info(products_ids=products_ids)
        products_config = self.__get_product_config()

        stock_entries = self._create_stock_portfolio_entries(portfolio_products, products_info, products_config)
        cash_entries = self._create_cash_portfolio_entries()

        return sorted(stock_entries + cash_entries, key=lambda k: k.symbol)

    def _create_stock_portfolio_entries(
        self, portfolio_products: list[dict], products_info: dict, products_config: dict
    ) -> List[PortfolioEntry]:
        """Create portfolio entries for stock/ETF products."""
        stock_entries = []
        processed_symbols = set()

        for product_data in portfolio_products:
            product_info = products_info[product_data[self.PRODUCT_ID_FIELD]]

            if product_info.get("productType") == self.CASH_PRODUCT_TYPE:
                continue

            symbol = product_info["symbol"]
            if symbol in processed_symbols:
                continue

            processed_symbols.add(symbol)

            # Get correlated products for the same symbol
            correlated_products = self._get_correlated_products(symbol)

            # Create portfolio entry
            entry = self._create_portfolio_entry(product_data, product_info, products_config, correlated_products)
            stock_entries.append(entry)

        return stock_entries

    def _get_correlated_products(self, symbol: str) -> list[str]:
        """Get all product IDs for the same symbol (handles reopened products)."""
        tmp_products = self.product_info.get_products_info_raw_by_symbol([symbol])
        return [p["id"] for p in tmp_products.values()]

    def _create_portfolio_entry(
        self, product_data: dict, product_info: dict, products_config: dict, correlated_products: list[str]
    ) -> PortfolioEntry:
        """Create a single portfolio entry from product data."""
        # Get company profile data
        company_data = self._get_company_data(product_info["isin"])

        # Calculate financial metrics
        total_realized_gains, total_costs = self.__get_product_realized_gains(correlated_products)

        # Get pricing information
        price_data = self._get_price_data(product_data, product_info)

        # Convert to base currency if needed
        base_currency_data = self._convert_to_base_currency(price_data, product_info["currency"])

        # Get exchange information
        exchange = self.__get_exchange(product_info["exchangeId"], products_config.get("exchanges", []))

        return PortfolioEntry(
            name=product_info["name"],
            symbol=product_info["symbol"],
            isin=product_info["isin"],
            sector=Sector.from_str(company_data["sector"]),
            industry=company_data["industry"],
            category=product_info["category"],
            exchange=exchange,
            country=Country(company_data["country"]) if company_data["country"] != "Unknown" else None,
            product_type=ProductType.from_str(product_info["productType"]),
            shares=product_data["size"],
            product_currency=product_info["currency"],
            price=price_data["price"],
            base_currency_price=base_currency_data["price"],
            base_currency=self.base_currency,
            break_even_price=price_data["break_even_price"],
            base_currency_break_even_price=base_currency_data["break_even_price"],
            value=price_data["value"],
            base_currency_value=base_currency_data["value"],
            is_open=price_data["is_open"],
            unrealized_gain=base_currency_data["unrealized_gain"],
            realized_gain=total_realized_gains,
            total_costs=total_costs,
        )

    def _get_company_data(self, isin: str) -> dict:
        """Extract company profile data with defaults."""
        company_profile = CompanyProfileRepository.get_company_profile_raw(isin)

        if not company_profile:
            self.logger.warning(f"No company profile found for ISIN {isin}, using defaults")

        if company_profile and company_profile.get("data"):
            return {
                "sector": company_profile["data"]["sector"],
                "industry": company_profile["data"]["industry"],
                "country": company_profile["data"]["contacts"]["COUNTRY"],
            }

        return {"sector": None, "industry": "Unknown", "country": "Unknown"}

    def _get_price_data(self, product_data: dict, product_info: dict) -> dict:
        """Get pricing information for a product."""
        price = ProductQuotationsRepository.get_product_price(product_data[self.PRODUCT_ID_FIELD])

        # Fallback to close price if no quotation found
        if price == self.FALLBACK_PRICE and self.CLOSE_PRICE_FIELD in product_info:
            self.logger.warning(
                f"No quotation found for '{product_info['symbol']}' "
                f"(productId {product_data[self.PRODUCT_ID_FIELD]}), using {self.CLOSE_PRICE_FIELD}"
            )
            price = product_info[self.CLOSE_PRICE_FIELD]

        value = product_data["size"] * price
        break_even_price = product_data.get("breakEvenPrice", 0.0)
        is_open = product_data["size"] != 0.0 and product_data["value"] != 0.0

        return {
            "price": price,
            "value": value,
            "break_even_price": break_even_price,
            "is_open": is_open,
            "size": product_data["size"],  # Include size for currency conversion
        }

    def _convert_to_base_currency(self, price_data: dict, currency: str) -> dict:
        """Convert price data to base currency."""
        size = price_data["size"]
        break_even_price = price_data.get("break_even_price", 0.0)
        if break_even_price is None:
            break_even_price = 0.0

        if currency == self.base_currency:
            return {
                "price": price_data["price"],
                "value": price_data["value"],
                "break_even_price": break_even_price,
                "unrealized_gain": (price_data["price"] - break_even_price) * size,
            }

        # Convert to base currency
        base_price = self.currency_service.convert(price_data["price"], currency, self.base_currency)
        base_value = self.currency_service.convert(price_data["value"], currency, self.base_currency)
        base_break_even = self.currency_service.convert(break_even_price, currency, self.base_currency)

        # Calculate unrealized gain in base currency
        unrealized_gain = (base_price - base_break_even) * size

        return {
            "price": base_price,
            "value": base_value,
            "break_even_price": base_break_even,
            "unrealized_gain": unrealized_gain,
        }

    def _create_cash_portfolio_entries(self) -> List[PortfolioEntry]:
        """Create portfolio entries for cash balances."""
        cash_entries = []

        for currency in self.SUPPORTED_CURRENCY_ACCOUNTS:
            total_cash = CashMovementsRepository.get_total_cash(currency)
            if total_cash is None:
                self.logger.debug(f"No cash movements found for currency {currency}, skipping")
                continue

            base_currency_value = total_cash
            if currency != self.base_currency:
                base_currency_value = self.currency_service.convert(total_cash, currency, self.base_currency)

            cash_entries.append(
                PortfolioEntry(
                    name=self.CASH_BALANCE_NAME_TEMPLATE.format(currency=currency),
                    symbol=currency,
                    product_type=ProductType.CASH,
                    product_currency=currency,
                    value=total_cash,
                    base_currency_value=base_currency_value,
                    base_currency=self.base_currency,
                    is_open=True,
                )
            )

        return cash_entries

    def __get_exchange(self, exchange_id: str, exchanges: list) -> str | None:
        """
        Get the exchange name from the exchange ID.
        """
        exchange = None
        if exchanges:
            degiro_exchange = next((ex for ex in exchanges if ex["id"] == int(exchange_id)), None)
            if degiro_exchange and "micCode" in degiro_exchange:
                mic_code = degiro_exchange["micCode"].lower()
                exchange = MIC[mic_code].value
        return exchange

    def __get_product_realized_gains(self, product_ids: list[str]) -> tuple[float, float]:
        data = self.transactions.get_product_transactions(product_ids)

        buys = [t for t in data if t["buysell"] == "B"]
        sells = [t for t in data if t["buysell"] == "S"]

        # Sort transactions by stock_id and transaction_date
        buys.sort(key=lambda x: x["date"])
        sells.sort(key=lambda x: x["date"])

        # FIFO matching logic
        realized_gains = []
        total_costs = sum([abs(b["quantity"]) * b["price"] for b in buys])
        total_realized_gains = 0.0
        for sell in sells:
            sell_qty = abs(sell["quantity"])
            sell_price = sell["price"]
            gains = 0.0

            # Match sells with existing buys using FIFO
            for buy in buys:
                if sell_qty <= 0:
                    break

                match_qty = min(sell_qty, buy["quantity"])
                gains += match_qty * (sell_price - buy["price"])

                # Update quantities
                buy["quantity"] -= match_qty
                sell_qty -= match_qty

                # Remove fully used buys
                if buy["quantity"] == 0:
                    buys.remove(buy)

            realized_gains.append({"sell_date": sell["date"], "realized_gain": gains})
            total_realized_gains += gains

        return total_realized_gains, total_costs

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        self.logger.debug("Get Portfolio Total")

        # Calculate current value
        if not portfolio:
            portfolio = self.get_portfolio

        portfolio_total_value = 0.0

        for entry in portfolio:
            if entry.is_open:
                portfolio_total_value += entry.base_currency_value

        total_deposit_withdrawal = CashMovementsRepository.get_total_cash_deposits_raw()
        total_cash = self.__get_total_cash()

        # Try to get the data directly from DeGiro, so we get up-to-date values
        realtime_total_portfolio = self.__get_realtime_portfolio_total()
        if realtime_total_portfolio:
            total_deposit_withdrawal = realtime_total_portfolio["totalDepositWithdrawal"]

        roi = (portfolio_total_value / total_deposit_withdrawal - 1) * 100
        total_profit_loss = portfolio_total_value - total_deposit_withdrawal

        return TotalPortfolio(
            base_currency=self.base_currency,
            total_pl=total_profit_loss,
            total_cash=total_cash,
            current_value=portfolio_total_value,
            total_roi=roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )

    def __get_total_cash(self) -> float:
        total_cash = 0.0
        for currency in self.SUPPORTED_CURRENCY_ACCOUNTS:
            cash = CashMovementsRepository.get_total_cash(currency)
            if cash is None:
                self.logger.debug(f"No cash movements found for currency {currency}, skipping")
                continue

            if currency != self.base_currency:
                cash = self.currency_service.convert(cash, currency, self.base_currency)
            total_cash += cash

        # Try to get the data directly from DeGiro, so we get up-to-date values
        realtime_total_portfolio = self.__get_realtime_portfolio_total()
        if realtime_total_portfolio:
            if "freeSpaceNew" in realtime_total_portfolio:
                total_cash = 0.0
                for currency, amount in realtime_total_portfolio["freeSpaceNew"].items():
                    if currency != self.base_currency:
                        amount = self.currency_service.convert(amount, currency, self.base_currency)
                    total_cash += amount
            else:
                total_cash = realtime_total_portfolio["totalCash"]

        return total_cash

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
        except (ConnectionError, TimeoutError, DeGiroOfflineModeError):
            self.logger.warning("Cannot get realtime portfolio total from DeGiro")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting realtime portfolio total: {e}")
            return None

    def __get_portfolio_products(self) -> list[dict]:
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
                                key = self.PRODUCT_ID_FIELD
                            portfolio[key] = value["value"]

                    my_portfolio.append(portfolio)
            return my_portfolio
        except DeGiroOfflineModeError:
            return self._get_local_portfolio(offline=True)
        except Exception:
            return self._get_local_portfolio(offline=False)

    def _get_local_portfolio(self, offline: bool = False):
        if offline:
            self.logger.info("Running in offline mode, using last known data")
        else:
            self.logger.warning("Cannot connect to DeGiro, getting last known data")
        local_portfolio = TransactionsRepository.get_portfolio_products()
        for entry in local_portfolio:
            entry["value"] = self.DEFAULT_PORTFOLIO_VALUE  # FIXME: Use actual portfolio value
        return local_portfolio

    def __get_products_info(self, products_ids: list) -> dict:
        # Handle offline mode immediately
        products_info: dict | None = None
        try:
            products_info = self.degiro_service.get_products_info(products_ids)
        except DeGiroOfflineModeError:
            self.logger.info("Running in offline mode, using last known data")
        except (ConnectionError, TimeoutError) as e:
            self.logger.warning(f"Cannot connect to DeGiro: {e}, getting last known data")
        except Exception as e:
            self.logger.error(f"Unexpected error getting products info: {e}")

        # Handle None result (internal failures were caught)
        if products_info is None:
            self.logger.warning("DeGiro service returned None, falling back to last known data")
            return ProductInfoRepository.get_products_info_raw(products_ids)

        return products_info

    def __get_product_config(self) -> dict:
        try:
            return self.degiro_service.get_client().get_products_config()
        except (ConnectionError, TimeoutError, DeGiroOfflineModeError):
            self.logger.warning("Cannot get product config from DeGiro")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error getting product config: {e}")
            return {}

    def calculate_product_growth(self) -> dict:
        self.logger.debug("Calculating Product growth")

        results = TransactionsRepository.get_products_transactions()

        product_growth = {}
        for entry in results:
            key = entry[self.PRODUCT_ID_FIELD]
            product = product_growth.get(key, {})
            carry_total = product.get("carryTotal", 0)

            stock_date = entry["date"].strftime(LocalizationUtility.DATE_FORMAT)
            carry_total += entry["quantity"]

            product["carryTotal"] = carry_total
            if "history" not in product:
                product["history"] = {}
            product["history"][stock_date] = carry_total
            product_growth[key] = product

        # Cleanup 'carry_total' from the result
        for key in product_growth.keys():
            del product_growth[key]["carryTotal"]

        return product_growth

    def calculate_historical_value(self) -> List[DailyValue]:
        self.logger.debug("Calculating historical value")

        cash_account = self.deposits.calculate_cash_account_value()
        data = self._create_products_quotation()

        aggregate = {}
        for key in data:
            entry = data[key]
            # ONLY the tradable products are considered for Growth
            if is_non_tradeable_product(entry["product"]):
                continue

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
        """Calculate position growth with stock split adjustments."""
        symbol = entry["product"]["symbol"]

        # Step 1: Build position values for all dates
        position_value = self._build_position_values(entry)

        # Step 2: Get and process stock splits
        stock_splits = self.yfinance.get_stock_splits(symbol)
        if stock_splits:
            position_value = self._apply_stock_split_adjustments(symbol, position_value, stock_splits)

        # Step 3: Calculate final aggregate values with quotes
        return self._calculate_aggregate_values(entry, position_value)

    def _build_position_values(self, entry: dict) -> dict:
        """Build position values for all dates between start and end."""
        product_history_dates = list(entry["history"].keys())
        start_date = LocalizationUtility.convert_string_to_date(product_history_dates[0])
        final_date = self._get_growth_final_date(product_history_dates[-1])

        # Generate complete date range
        dates = [
            (start_date + timedelta(days=i)).strftime(LocalizationUtility.DATE_FORMAT)
            for i in range((final_date - start_date).days + 1)
        ]

        # Fill position values for all dates
        position_value = {}
        for date_change in entry["history"]:
            index = dates.index(date_change)
            for d in dates[index:]:
                position_value[d] = entry["history"][date_change]

        return position_value

    def _apply_stock_split_adjustments(self, symbol: str, position_value: dict, stock_splits: list) -> dict:
        """Apply stock split adjustments to position values."""
        # Detect effective split dates to handle timing mismatches
        effective_split_dates = self._detect_effective_split_dates(symbol, position_value, stock_splits)

        # Log debug information if this is the target symbol
        self._log_split_debug_info(symbol, stock_splits, effective_split_dates)

        # Apply split adjustments to each date
        for date_value in reversed(position_value):
            multiplier = self._calculate_split_multiplier(symbol, date_value, stock_splits, effective_split_dates)
            position_value[date_value] *= multiplier

        return position_value

    def _calculate_split_multiplier(
        self, symbol: str, date_value: str, stock_splits: list, effective_split_dates: dict
    ) -> float:
        """Calculate the cumulative split multiplier for a specific date."""
        multiplier = 1.0
        should_log = self._should_log_debug(symbol, date_value)

        if should_log:
            self.logger.debug(f"[{symbol} DEBUG] Processing date {date_value}")

        for split_data in reversed(stock_splits):
            split_date_str = LocalizationUtility.format_date_from_date(split_data.date.astimezone(ZoneInfo(TIME_ZONE)))

            # Use effective split date if detected
            effective_split_date = effective_split_dates.get(split_date_str, split_date_str)

            if effective_split_date != split_date_str and should_log:
                self.logger.debug(
                    f"[{symbol} DEBUG]   Using effective split date {effective_split_date} instead of {split_date_str}"
                )

            # Apply split if the effective date is after the current date
            if effective_split_date > date_value:
                multiplier *= split_data.split_ratio
                if should_log:
                    self.logger.debug(
                        f"[{symbol} DEBUG]   Applying split: "
                        f"{effective_split_date} > {date_value}, "
                        f"ratio={split_data.split_ratio}, multiplier now={multiplier}"
                    )
            elif should_log:
                self.logger.debug(f"[{symbol} DEBUG]   Skipping split: {effective_split_date} <= {date_value}")

        if should_log and multiplier != 1:
            self.logger.debug(f"[{symbol} DEBUG]   Total multiplier: {multiplier}")

        return multiplier

    def _calculate_aggregate_values(self, entry: dict, position_value: dict) -> dict:
        """Calculate final aggregate values by multiplying positions with quotes."""
        aggregate = {}
        symbol = entry["product"]["symbol"]

        if entry["quotation"]["quotes"]:
            for date_quote in entry["quotation"]["quotes"]:
                if date_quote in position_value:
                    aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]
        else:
            self.logger.warning(f"No quotes found for '{symbol}': productId {entry['productId']}")

        return aggregate

    def _log_split_debug_info(self, symbol: str, stock_splits: list, effective_split_dates: dict):
        """Log debug information for stock splits if this is the target symbol."""
        if not self._is_debug_symbol(symbol):
            return

        self.logger.debug(f"[{symbol} DEBUG] Processing stock splits for {symbol}")
        self.logger.debug(f"[{symbol} DEBUG] Found {len(stock_splits)} stock splits")

        if effective_split_dates:
            self.logger.debug(f"[{symbol} DEBUG] Detected effective split dates: {effective_split_dates}")

        # Log all stock splits
        for i, split in enumerate(stock_splits):
            split_date_str = LocalizationUtility.format_date_from_date(split.date.astimezone(ZoneInfo(TIME_ZONE)))
            self.logger.debug(f"[{symbol} DEBUG] Split {i + 1}: Date={split_date_str}, Ratio={split.split_ratio}")

    def _is_debug_symbol(self, symbol: str) -> bool:
        """Check if this symbol should have debug logging enabled."""
        return symbol == self.DEBUG_SYMBOL

    def _should_log_debug(self, symbol: str, date_value: str) -> bool:
        """Check if debug logging should be enabled for this symbol and date."""
        if not self._is_debug_symbol(symbol):
            return False

        return date_value in self.DEBUG_DATES

    def _detect_effective_split_dates(self, symbol: str, position_value: dict, stock_splits: list) -> dict:
        """
        Detect when position data already includes split effects by analyzing position value jumps.

        Args:
            position_value: Dictionary of {date: shares}
            stock_splits: List of StockSplit objects

        Returns:
            Dictionary mapping official split dates to detected effective split dates
        """
        if not stock_splits:
            return {}

        effective_split_dates = {}

        # Convert to sorted list of (date, value) pairs
        sorted_positions = sorted(position_value.items())

        for split in stock_splits:
            split_date_str = LocalizationUtility.format_date_from_date(split.date.astimezone(ZoneInfo(TIME_ZONE)))
            split_ratio = split.split_ratio

            # Look for jumps in position values that match the split ratio
            # Check a window around the official split date (±5 days)
            split_date_obj = LocalizationUtility.convert_string_to_date(split_date_str)

            for i in range(1, len(sorted_positions)):
                prev_date_str, prev_value = sorted_positions[i - 1]
                curr_date_str, curr_value = sorted_positions[i]

                # Skip if values are zero or negative
                if prev_value <= 0 or curr_value <= 0:
                    continue

                # Check if this position change date is within ±5 days of the split date
                curr_date_obj = LocalizationUtility.convert_string_to_date(curr_date_str)
                days_diff = abs((curr_date_obj - split_date_obj).days)

                if days_diff > 5:
                    continue

                # Calculate the ratio of position change
                ratio = curr_value / prev_value

                # Check if this ratio matches the split ratio (within 10% tolerance)
                # Allow for both forward and reverse splits
                ratio_tolerance = 0.1
                if (
                    abs(ratio - split_ratio) / split_ratio < ratio_tolerance
                    or abs(ratio - (1 / split_ratio)) / (1 / split_ratio) < ratio_tolerance
                ):
                    # Found a jump that matches the split ratio
                    # The effective split date is the current date (when the jump happens)
                    effective_split_dates[split_date_str] = curr_date_str
                    self.logger.debug(
                        f"[{symbol}] Detected effective split date: {split_date_str} -> {curr_date_str} "
                        f"(ratio: {ratio:.2f}, expected: {split_ratio})"
                    )
                    break

        return effective_split_dates

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
            if self.NON_TRADEABLE_IDENTIFIER in product.get("name", ""):
                continue

            data[self.PRODUCT_ID_FIELD] = key
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
        day = datetime.strptime(date_str, "%Y-%m-%d")
        # Check if the day of the week is Saturday (5) or Sunday (6)
        return day.weekday() >= 5
