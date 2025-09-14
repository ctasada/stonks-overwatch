import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

import polars as pl
from degiro_connector.quotecast.models.chart import Interval
from degiro_connector.trading.models.account import OverviewRequest
from degiro_connector.trading.models.transaction import HistoryRequest
from django.core.cache import cache
from django.db import connection

from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.degiro.client.constants import CurrencyFX
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.brokers.degiro.repositories.models import (
    DeGiroAgendaDividend,
    DeGiroCashMovements,
    DeGiroCompanyProfile,
    DeGiroProductInfo,
    DeGiroProductQuotation,
    DeGiroTransactions,
    DeGiroUpcomingPayments,
)
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_quotations_repository import (
    ProductQuotationsRepository,
)
from stonks_overwatch.services.brokers.degiro.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.brokers.degiro.services.helper import is_non_tradeable_product
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService
from stonks_overwatch.services.brokers.degiro.services.session_checker import DeGiroSessionChecker
from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import YFinanceClient
from stonks_overwatch.services.brokers.yfinance.repositories.models import YFinanceStockSplits, YFinanceTickerInfo
from stonks_overwatch.utils.core.datetime import DateTimeUtility
from stonks_overwatch.utils.core.debug import save_to_json
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.database.db_utils import dictfetchall
from stonks_overwatch.utils.domain.constants import ProductType

CACHE_KEY_UPDATE_PORTFOLIO = "portfolio_data_update_from_degiro"
CACHE_KEY_UPDATE_COMPANIES = "company_profile_update_from_degiro"
CACHE_KEY_UPDATE_YFINANCE = "yfinance_update"
# Cache the result for 1 hour (3600 seconds)
CACHE_TIMEOUT = 3600


class UpdateService(BaseService, AbstractUpdateService):
    def __init__(
        self,
        import_folder: str = None,
        debug_mode: bool = None,
        config: Optional[DegiroConfig] = None,
        force_connect: bool = False,
    ):
        """
        Initialize the UpdateService.
        :param import_folder:
            Folder to store the JSON files for debugging purposes.
        :param debug_mode:
            If True, the service will store the JSON files for debugging purposes.
        :param config:
            Optional configuration instance for dependency injection.
        :param force_connect:
            If True, the service will attempt to connect to DeGiro upon initialization.
        """
        # Initialize AbstractUpdateService first (has no super() calls to interfere)
        AbstractUpdateService.__init__(self, "DEGIRO", import_folder, debug_mode, config)
        # Then manually set BaseService attributes without calling its __init__
        self._global_config = None
        self._injected_config = config
        if self._injected_config is None:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            self._injected_config = broker_factory.create_config("degiro")

        # Pass injected config to DeGiro service for proper credential access
        self.degiro_service = DeGiroService(config=self._injected_config)

        if force_connect:
            self.degiro_service.connect()

        self.portfolio_data = PortfolioService(
            degiro_service=self.degiro_service,
        )
        self.yfinance_client = YFinanceClient()

    def get_last_import(self) -> datetime:
        last_cash_movement = self._get_last_cash_movement_import()
        last_transaction = self._get_last_transactions_import()
        last_quotation = ProductQuotationsRepository.get_last_update()

        return max([last_cash_movement, last_transaction, last_quotation])

    def _get_last_cash_movement_import(self) -> datetime:
        last_movement = CashMovementsRepository.get_last_movement()
        if last_movement is None:
            degiro_config = self._injected_config

            if degiro_config:
                last_movement = datetime.combine(degiro_config.start_date, time.min)
            else:
                # Fallback to a reasonable default if no config available
                last_movement = datetime.now() - timedelta(days=365)

        return last_movement

    def _get_last_transactions_import(self) -> datetime:
        last_movement = TransactionsRepository.get_last_movement()
        if last_movement is None:
            degiro_config = self._injected_config

            if degiro_config:
                last_movement = datetime.combine(degiro_config.start_date, time.min)
            else:
                # Fallback to a reasonable default if no config available
                last_movement = datetime.now() - timedelta(days=365)

        return last_movement

    def update_all(self):
        if not DeGiroSessionChecker.has_active_session():
            self.logger.warning("Skipping update: No active DeGiro session available")
            self.logger.info("Please authenticate first to establish a session")
            return

        if not self.degiro_service.check_connection():
            self.logger.warning("Skipping update since cannot connect to DeGiro")
            return

        if self.debug_mode:
            self.logger.info("Storing JSON files at %s", self.import_folder)

        try:
            self.update_account()
            self.update_transactions()
            self.update_portfolio()
            self.update_company_profile()
            self.update_yfinance()
            self.update_dividends()
        except Exception as error:
            self.logger.error("Cannot Update Portfolio!")
            self.logger.error("Exception: %s", str(error), exc_info=True)

    def update_account(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Account Data....")

        now = LocalizationUtility.now()
        last_movement = self._get_last_cash_movement_import().replace(tzinfo=timezone.utc)

        if last_movement >= now:
            return

        account_overview = self.__get_cash_movements(last_movement.date())
        if self.debug_mode:
            account_file = os.path.join(self.import_folder, "account.json")
            save_to_json(account_overview, account_file)

        transformed_data = self.__transform_json(account_overview)
        if self.debug_mode:
            save_to_json(transformed_data, os.path.join(self.import_folder, "account_transform.json"))

        self.__import_cash_movements(transformed_data)

    def update_transactions(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Transactions Data....")

        now = LocalizationUtility.now()
        last_movement = self._get_last_transactions_import().replace(tzinfo=timezone.utc)

        if last_movement >= now:
            return

        transactions_history = self.__get_transaction_history(last_movement.date())

        if self.debug_mode:
            transactions_file = os.path.join(self.import_folder, "transactions.json")
            save_to_json(transactions_history, transactions_file)

        self.__import_transactions(transactions_history)

    def update_portfolio(self):
        """Updating the Portfolio is an expensive and time-consuming task.
        This method caches the result for a period of time.
        """
        self._log_message("Updating Portfolio Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_PORTFOLIO)

        # If a result is already cached, return it
        if cached_data is None:
            self._log_message("Portfolio data not found in cache. Calling DeGiro")
            # Otherwise, call the expensive method
            result = self.__update_portfolio()

            cache.set(CACHE_KEY_UPDATE_PORTFOLIO, result, timeout=CACHE_TIMEOUT)

            return result

        return cached_data

    def update_company_profile(self):
        """Updating the Company Profiles is an expensive and time-consuming task.
        This method caches the result for a period of time.
        """
        self._log_message("Updating Company Profiles Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_COMPANIES)

        # If a result is already cached, return it
        if cached_data is None:
            self._log_message("Companies Profile data not found in cache. Calling DeGiro")
            # Otherwise, call the expensive method
            result = self.__update_company_profile()

            cache.set(CACHE_KEY_UPDATE_COMPANIES, result, timeout=CACHE_TIMEOUT)

            return result

        return cached_data

    def __update_portfolio(self):
        """Update the Portfolio DB data."""
        product_ids = self.__get_product_ids()

        products_info = self.__get_products_info(product_ids)
        if self.debug_mode:
            products_info_file = os.path.join(self.import_folder, "products_info.json")
            save_to_json(products_info, products_info_file)

        self.__import_products_info(products_info)
        self.__import_products_quotation()

    def __update_company_profile(self) -> dict:
        company_profiles = self.__get_company_profiles()
        if self.debug_mode:
            company_profiles_file = os.path.join(self.import_folder, "company_profiles.json")
            save_to_json(company_profiles, company_profiles_file)

        self.__import_company_profiles(company_profiles)

        return company_profiles

    def __get_cash_movements(self, from_date: date) -> dict:
        """Import Account data from DeGiro. Uses the `get_account_overview` method.

        ### Parameters
            * from_date : date
                - Starting date to import the data
        ### Returns:
            account information
        """
        trading_api = self.degiro_service.get_client()

        request = OverviewRequest(from_date=from_date, to_date=date.today())

        # FETCH DATA
        account_overview = trading_api.get_account_overview(
            overview_request=request,
            raw=True,
        )

        return account_overview

    def __get_products_info(self, products_ids: list) -> dict:
        return self.degiro_service.get_products_info(products_ids)

    def __conv(self, i):
        return i or None

    def __import_cash_movements(self, cash_data: list[dict]) -> None:
        """Store the cash movements into the DB."""

        if cash_data:
            for row in cash_data:
                try:
                    self._retry_database_operation(
                        DeGiroCashMovements.objects.update_or_create,
                        id=row["id"],
                        defaults={
                            "date": LocalizationUtility.convert_string_to_datetime(row["date"]),
                            "value_date": LocalizationUtility.convert_string_to_datetime(row["valueDate"]),
                            "description": row["description"],
                            "product_id": row.get("productId"),
                            "currency": row["currency"],
                            "type": row["type"],
                            "change": self.__conv(row.get("change", None)),
                            "balance_unsettled_cash": row.get("balance_unsettledCash", None),
                            "balance_flatex_cash": row.get("balance_flatexCash", None),
                            "balance_cash_fund": row.get("balance_cashFund", None),
                            "balance_total": row.get("balance_total", None),
                            "exchange_rate": self.__conv(row.get("exchangeRate", None)),
                            "order_id": row.get("orderId", None),
                        },
                    )
                except Exception as error:
                    self.logger.error(f"Cannot import row: {row}")
                    self.logger.error("Exception: %s", str(error))

    def __transform_json(self, account_overview: dict) -> list[dict] | None:
        """Flattens the data from deGiro `get_account_overview`."""

        def _flatten_json(data: list[dict], sep: str = "_") -> list[dict]:
            """Manually flatten nested JSON data similar to pd.json_normalize."""
            flattened = []
            for item in data:
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, dict):
                        # Flatten nested dictionaries
                        for nested_key, nested_value in value.items():
                            flat_item[f"{key}{sep}{nested_key}"] = nested_value
                    else:
                        flat_item[key] = value
                flattened.append(flat_item)
            return flattened

        def _fix_columns(dataframe: pl.DataFrame, columns: list[str], func) -> pl.DataFrame:
            """Apply a function to specified columns."""
            for col in columns:
                if col in dataframe.columns:
                    dataframe = dataframe.with_columns(
                        pl.col(col).map_elements(func, return_dtype=pl.String).alias(col)
                    )
            return dataframe

        if account_overview.get("data") and account_overview["data"].get("cashMovements"):
            # Flatten the JSON data manually
            flattened_data = _flatten_json(account_overview["data"]["cashMovements"], sep="_")
            df = pl.DataFrame(flattened_data)

            # Fix id values format
            df = _fix_columns(
                df,
                ["productId", "id", "exchangeRate", "orderId"],
                lambda x: None if (x is None) else str(x).replace(".0", ""),
            )
            df = _fix_columns(df, ["change"], lambda x: None if (x is None) else str(x))

            # Sort the DataFrame by the 'date' column
            df = df.sort("date")

            return df.to_dicts()
        return None

    def __get_transaction_history(self, from_date: date) -> dict:
        """Import Transactions data from DeGiro. Uses the `get_transactions_history` method."""
        trading_api = self.degiro_service.get_client()

        # FETCH DATA
        return trading_api.get_transactions_history(
            transaction_request=HistoryRequest(from_date=from_date, to_date=date.today()),
            raw=True,
        )

    def __import_transactions(self, transactions_history: dict) -> None:
        """Store the Transactions into the DB."""

        for row in transactions_history["data"]:
            try:
                self._retry_database_operation(
                    DeGiroTransactions.objects.update_or_create,
                    id=row["id"],
                    defaults={
                        "product_id": row["productId"],
                        "date": LocalizationUtility.convert_string_to_datetime(row["date"]),
                        "buysell": row["buysell"],
                        "price": row["price"],
                        "quantity": row["quantity"],
                        "total": row["total"],
                        "order_type_id": row.get("orderTypeId", None),
                        "counter_party": row.get("counterParty", None),
                        "transfered": row["transfered"],
                        "fx_rate": row["fxRate"],
                        "nett_fx_rate": row["nettFxRate"],
                        "gross_fx_rate": row["grossFxRate"],
                        "auto_fx_fee_in_base_currency": row["autoFxFeeInBaseCurrency"],
                        "total_in_base_currency": row["totalInBaseCurrency"],
                        "fee_in_base_currency": row.get("feeInBaseCurrency", None),
                        "total_fees_in_base_currency": row["totalFeesInBaseCurrency"],
                        "total_plus_fee_in_base_currency": row["totalPlusFeeInBaseCurrency"],
                        "total_plus_all_fees_in_base_currency": row["totalPlusAllFeesInBaseCurrency"],
                        "transaction_type_id": row["transactionTypeId"],
                        "trading_venue": row.get("tradingVenue", None),
                        "executing_entity_id": row.get("executingEntityId", None),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import row: {row}")
                self.logger.error("Exception: %s", str(error))

    def __get_product_ids(self) -> list:
        """Get the list of product ids from the DB.

        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT product_id FROM degiro_transactions
                UNION
                SELECT product_id FROM degiro_cashmovements
                """
            )
            results = dictfetchall(cursor)

        product_ids = [str(entry["productId"]) for entry in results if entry["productId"] is not None]
        product_ids = list(dict.fromkeys(product_ids))
        # Adding Currencies to the list, so we can do FX
        product_ids.extend(CurrencyFX.to_str_list())

        return product_ids

    def __import_products_info(self, products_info: dict) -> None:
        """Store the product information into the DB."""

        for key in products_info:
            row = products_info[key]
            try:
                self._retry_database_operation(
                    DeGiroProductInfo.objects.update_or_create,
                    id=int(row["id"]),
                    defaults={
                        "name": row["name"],
                        "isin": row["isin"],
                        "symbol": row["symbol"],
                        "contract_size": row["contractSize"],
                        "product_type": row["productType"],
                        "product_type_id": row["productTypeId"],
                        "tradable": row["tradable"],
                        "category": row["category"],
                        "currency": row["currency"],
                        "active": row["active"],
                        "exchange_id": row["exchangeId"],
                        "only_eod_prices": row["onlyEodPrices"],
                        "is_shortable": row.get("isShortable", False),
                        "feed_quality": row.get("feedQuality"),
                        "order_book_depth": row.get("orderBookDepth"),
                        "vwd_identifier_type": row.get("vwdIdentifierType"),
                        "vwd_id": row.get("vwdId"),
                        "quality_switchable": row.get("qualitySwitchable"),
                        "quality_switch_free": row.get("qualitySwitchFree"),
                        "vwd_module_id": row.get("vwdModuleId"),
                        "feed_quality_secondary": row.get("feedQualitySecondary"),
                        "order_book_depth_secondary": row.get("orderBookDepthSecondary"),
                        "vwd_identifier_type_secondary": row.get("vwdIdentifierTypeSecondary"),
                        "vwd_id_secondary": row.get("vwdIdSecondary"),
                        "quality_switchable_secondary": row.get("qualitySwitchableSecondary"),
                        "quality_switch_free_secondary": row.get("qualitySwitchFreeSecondary"),
                        "vwd_module_id_secondary": row.get("vwdModuleIdSecondary"),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import row: {row}")
                self.logger.error("Exception: %s", str(error))

    def __import_products_quotation(self) -> None:  # noqa: C901
        product_growth = self.portfolio_data.calculate_product_growth()

        degiro_config = self._injected_config

        if degiro_config and hasattr(degiro_config, "start_date"):
            start_date = degiro_config.start_date.strftime(LocalizationUtility.DATE_FORMAT)
        else:
            # Fallback to a reasonable default date if config is unavailable
            from datetime import datetime, timedelta

            default_start = datetime.now() - timedelta(days=365)  # 1 year ago
            start_date = default_start.strftime(LocalizationUtility.DATE_FORMAT)
        for currency in CurrencyFX.to_list():
            if currency not in product_growth:
                product_growth[currency] = {"history": {}}
                product_growth[currency]["history"][start_date] = 1

        delete_keys = []
        today = LocalizationUtility.format_date_from_date(date.today())

        for key in product_growth.keys():
            product = ProductInfoRepository.get_product_info_from_id(key)

            # FIXME: Code copied from dashboard._create_products_quotation()
            if is_non_tradeable_product(product):
                delete_keys.append(key)
                continue

            product_growth[key]["product"] = {}
            product_growth[key]["product"]["name"] = product["name"]
            product_growth[key]["product"]["isin"] = product["isin"]
            product_growth[key]["product"]["symbol"] = product["symbol"]
            product_growth[key]["product"]["currency"] = product["currency"]
            product_growth[key]["product"]["vwdId"] = product["vwdId"]
            product_growth[key]["product"]["vwdIdSecondary"] = product["vwdIdSecondary"]

            # Calculate Quotation Range
            product_growth[key]["quotation"] = {}
            product_history_dates = list(product_growth[key]["history"].keys())
            start_date = product_history_dates[0]
            final_date = today
            tmp_last = product_history_dates[-1]
            if product_growth[key]["history"][tmp_last] == 0:
                final_date = tmp_last

            product_growth[key]["quotation"]["from_date"] = start_date
            product_growth[key]["quotation"]["to_date"] = final_date
            # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
            product_growth[key]["quotation"]["interval"] = DateTimeUtility.calculate_interval(start_date)

        # Delete the non-tradable products
        for key in delete_keys:
            del product_growth[key]

        # We need to use the productIds to get the daily quote for each product
        for key in product_growth.keys():
            symbol = product_growth[key]["product"]["symbol"]
            isin = product_growth[key]["product"]["isin"]
            if product_growth[key]["product"].get("vwdIdSecondary") is not None:
                issue_id = product_growth[key]["product"].get("vwdIdSecondary")
            else:
                issue_id = product_growth[key]["product"].get("vwdId")

            interval = product_growth[key]["quotation"]["interval"]
            quotes_dict = self.degiro_service.get_product_quotation(issue_id, isin, interval, symbol)

            if not quotes_dict:
                self.logger.info(f"Quotation not found for '{symbol}' ({key}): {issue_id} / {interval}")
                continue

            # Update the data ONLY if we get something back from DeGiro
            if quotes_dict:
                self._retry_database_operation(
                    DeGiroProductQuotation.objects.update_or_create,
                    id=int(key),
                    defaults={
                        "interval": Interval.P1D,
                        "last_import": LocalizationUtility.now(),
                        "quotations": quotes_dict,
                    },
                )

    def __get_company_profiles(self) -> dict:
        """Import Company Profiles data from DeGiro. Uses the `get_transactions_history` method."""
        products_isin = ProductInfoRepository.get_products_isin()

        company_profiles = {}

        for isin in products_isin:
            company_profile = self.degiro_service.get_client().get_company_profile(
                product_isin=isin,
                raw=True,
            )
            company_profiles[isin] = company_profile

        return company_profiles

    def __import_company_profiles(self, company_profiles: dict) -> None:
        """Store the Company Profiles into the DB.

        ### Parameters
            * file_path : str
                - Path to the JSON file that stores the company profiles
        ### Returns:
            None.
        """

        for key in company_profiles:
            try:
                self._retry_database_operation(
                    DeGiroCompanyProfile.objects.update_or_create, isin=key, defaults={"data": company_profiles[key]}
                )
            except Exception as error:
                self.logger.error(f"Cannot import ISIN: {key}")
                self.logger.error("Exception: %s", str(error))

    def update_yfinance(self):
        """Updating the Yahoo Finance Data."""
        self._log_message("Updating Yahoo Finance Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_YFINANCE)

        # If a result is already cached, return it
        if cached_data is None:
            self._log_message("Yahoo Finance data not found in cache. Calling YFinance")
            # Otherwise, call the expensive method
            result = self.__update_yfinance()

            cache.set(CACHE_KEY_UPDATE_YFINANCE, result, timeout=CACHE_TIMEOUT)

            return result

        return cached_data

    def __update_yfinance(self) -> Dict[str, dict]:
        # Get the list of DeGiro Products
        symbols = self.__get_symbols()

        tickers: Dict[str, dict] = {}
        splits = {}
        for symbol in symbols:
            try:
                yfinance_ticker = self.yfinance_client.get_ticker(symbol)
                splits_data = self.yfinance_client.get_stock_splits(yfinance_ticker)

                if yfinance_ticker is not None:
                    tickers[symbol] = yfinance_ticker.info
                    splits[symbol] = [split.to_dict() for split in splits_data]
                else:
                    tickers[symbol] = {}
                    splits[symbol] = []
            except Exception as error:
                self.logger.error(f"Cannot import symbol {symbol}: {error}")
                tickers[symbol] = {}
                splits[symbol] = []

        if self.debug_mode:
            yfinance_tickers_file = os.path.join(self.import_folder, "yfinance_tickers.json")
            save_to_json(tickers, yfinance_tickers_file)

            yfinance_splits_file = os.path.join(self.import_folder, "yfinance_splits.json")
            save_to_json(splits, yfinance_splits_file)

        self.__import_yfinance_tickers(tickers)
        self.__import_yfinance_splits(splits)

        return tickers

    def __get_symbols(self) -> list[str]:
        """Get the list of tickets to query with YFinance.

        ### Returns
            list: list of ticket symbols
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT symbol FROM degiro_productinfo WHERE product_type IN ('STOCK', 'ETF');
                """
            )
            result = dictfetchall(cursor)

            symbol_list = [row["symbol"] for row in result]
            return list(set(symbol_list))

    def __import_yfinance_tickers(self, tickers: Dict[str, dict]) -> None:
        """Store the Yahoo Finance Tickers into the DB."""

        for key in tickers:
            try:
                self._retry_database_operation(
                    YFinanceTickerInfo.objects.update_or_create, symbol=key, defaults={"data": tickers[key]}
                )
            except Exception as error:
                self.logger.error(f"Cannot import Ticker: {key}")
                self.logger.error("Exception: %s", str(error))

    def __import_yfinance_splits(self, splits: Dict[str, List[dict]]) -> None:
        """Store the Yahoo Finance Stock Splits into the DB."""

        for key in splits:
            try:
                self._retry_database_operation(
                    YFinanceStockSplits.objects.update_or_create, symbol=key, defaults={"data": splits[key]}
                )
            except Exception as error:
                self.logger.error(f"Cannot import Splits: {key}")
                self.logger.error("Exception: %s", str(error))

    def update_dividends(self):
        """Update the dividends data from DeGiro."""
        self._log_message("Updating Dividends Data....")

        upcoming_dividends = self.__get_upcoming_dividends()
        if self.debug_mode:
            upcoming_dividends_file = os.path.join(self.import_folder, "upcoming_dividends.json")
            save_to_json(upcoming_dividends, upcoming_dividends_file)

        self.__import_upcoming_dividends(upcoming_dividends["data"])

        agenda = self.__get_agenda()
        if self.debug_mode:
            agenda_file = os.path.join(self.import_folder, "agenda.json")
            save_to_json(agenda, agenda_file)

        self.__import_agenda(agenda)

    def __get_upcoming_dividends(self) -> List[Dict]:
        """Get the upcoming dividends from DeGiro."""
        trading_api = self.degiro_service.get_client()

        # FETCH DATA
        upcoming_dividends = trading_api.get_upcoming_payments(raw=True)

        if not upcoming_dividends:
            self.logger.info("No upcoming dividends found.")
            return []

        return upcoming_dividends

    def __get_agenda(self) -> List[Dict]:
        """Get the dividend agenda from DeGiro."""
        portfolio = self.portfolio_data.get_portfolio

        results = []
        for entry in portfolio:
            if entry.is_open and entry.product_type == ProductType.STOCK:
                forecasted_dividends = self.degiro_service.get_dividends_agenda(
                    company_name=entry.name, isin=entry.isin
                )
                if forecasted_dividends is not None:
                    results.append(forecasted_dividends)

        return results

    def __import_upcoming_dividends(self, upcoming_dividends: List[Dict]) -> None:
        """Store the upcoming dividends into the DB."""

        # Clear the existing upcoming dividends
        DeGiroUpcomingPayments.objects.all().delete()

        for entry in upcoming_dividends:
            try:
                DeGiroUpcomingPayments.objects.create(
                    ca_id=entry["caId"],
                    product=entry["product"],
                    description=entry["description"],
                    currency=entry["currency"],
                    amount=entry["amount"],
                    amount_in_base_curr=entry["amountInBaseCurr"],
                    pay_date=LocalizationUtility.convert_string_to_date(entry["payDate"]),
                )
            except Exception as error:
                self.logger.error(f"Cannot import upcoming dividend: {entry}")
                self.logger.error("Exception: %s", str(error))

    def __import_agenda(self, agenda: List[Dict]) -> None:
        """Store the dividend agenda into the DB."""
        # Clear the existing upcoming dividends
        DeGiroAgendaDividend.objects.all().delete()

        for entry in agenda:
            try:
                self._retry_database_operation(
                    DeGiroAgendaDividend.objects.update_or_create,
                    event_id=entry["eventId"],
                    defaults={
                        "isin": entry["isin"],
                        "ric": entry["ric"],
                        "organization_name": entry["organizationName"],
                        "date_time": LocalizationUtility.convert_string_to_datetime(entry["dateTime"]),
                        "last_update": LocalizationUtility.convert_string_to_datetime(entry["lastUpdate"]),
                        "country_code": entry["countryCode"],
                        "event_type": entry["eventType"],
                        "ex_dividend_date": LocalizationUtility.convert_string_to_datetime(entry["exDividendDate"]),
                        "payment_date": LocalizationUtility.convert_string_to_datetime(entry["paymentDate"]),
                        "dividend": entry.get("dividend", 0.0),
                        "yield_value": entry.get("yieldValue", 0.0),
                        "currency": entry["currency"],
                        "market_cap": entry.get("marketCap", ""),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import agenda dividend: {entry}")
                self.logger.error("Exception: %s", str(error))
