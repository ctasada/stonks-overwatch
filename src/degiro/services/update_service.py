import logging
from datetime import date, datetime, time, timezone

import pandas as pd
from degiro_connector.quotecast.models.chart import Interval
from degiro_connector.trading.models.account import OverviewRequest
from degiro_connector.trading.models.transaction import HistoryRequest
from django.core.cache import cache
from django.db import connection

from degiro.config.degiro_config import DegiroConfig
from degiro.models import CashMovements, CompanyProfile, ProductInfo, ProductQuotation, Transactions
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService
from degiro.utils.constants import CurrencyFX
from degiro.utils.datetime import DateTimeUtility
from degiro.utils.db_utils import dictfetchall
from degiro.utils.debug import save_to_json
from degiro.utils.localization import LocalizationUtility

CACHE_KEY_UPDATE_PORTFOLIO = "portfolio_data_update_from_degiro"
CACHE_KEY_UPDATE_COMPANIES = "company_profile_update_from_degiro"


class UpdateService:
    logger = logging.getLogger("stocks_portfolio.update_service")

    def __init__(self):
        self.degiro_service = DeGiroService()

        self.portfolio_data = PortfolioService(
            degiro_service=self.degiro_service,
        )

    def get_last_import(self) -> datetime:
        last_cash_movement = self._get_last_cash_movement_import()
        last_transaction = self._get_last_transactions_import()
        last_quotation = ProductQuotationsRepository.get_last_update()

        return max([last_cash_movement, last_transaction, last_quotation])

    def _get_last_cash_movement_import(self) -> datetime:
        last_movement = CashMovementsRepository.get_last_movement()
        if last_movement is None:
            last_movement = datetime.combine(DegiroConfig.default().start_date, time.min)

        return last_movement

    def _get_last_transactions_import(self) -> datetime:
        last_movement = TransactionsRepository.get_last_movement()
        if last_movement is None:
            last_movement = datetime.combine(DegiroConfig.default().start_date, time.min)

        return last_movement

    def update_all(self):
        self.update_account()
        self.update_transactions()
        self.update_portfolio()
        self.update_company_profile()

    def update_account(self, debug_json_files: dict = None):
        """Update the Account DB data. Only does it if the data is older than today."""
        self.logger.info("Updating Account Data....")

        now = LocalizationUtility.now()
        last_movement = self._get_last_cash_movement_import().replace(tzinfo=timezone.utc)

        if last_movement < now:
            account_overview = self.__get_cash_movements(last_movement.date())
            if debug_json_files and "account.json" in debug_json_files:
                save_to_json(account_overview, debug_json_files["account.json"])

            transformed_data = self.__transform_json(account_overview)
            if debug_json_files and "account_transform.json" in debug_json_files:
                save_to_json(transformed_data, debug_json_files["account_transform.json"])

            self.__import_cash_movements(transformed_data)

    def update_transactions(self, debug_json_files: dict = None):
        """Update the Account DB data. Only does it if the data is older than today."""
        self.logger.info("Updating Transactions Data....")

        now = LocalizationUtility.now()
        last_movement = self._get_last_transactions_import().replace(tzinfo=timezone.utc)

        if last_movement < now:
            transactions_history = self.__get_transaction_history(last_movement.date())
            if debug_json_files and "transactions.json" in debug_json_files:
                save_to_json(transactions_history, debug_json_files["transactions.json"])

            self.__import_transactions(transactions_history)

    def update_portfolio(self, debug_json_files: dict = None):
        """Updating the Portfolio is a expensive and time consuming task.
        This method caches the result for a period of time.
        """
        self.logger.info("Updating Portfolio Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_PORTFOLIO)

        # If result is already cached, return it
        if cached_data is None:
            self.logger.info("Portfolio data not found in cache. Calling DeGiro")
            # Otherwise, call the expensive method
            result = self.__update_portfolio(debug_json_files)

            # Cache the result for 1 hour (3600 seconds)
            cache.set(CACHE_KEY_UPDATE_PORTFOLIO, result, timeout=3600)

            return result

        return cached_data

    def update_company_profile(self, debug_json_files: dict = None):
        """Updating the Company Profiles is a expensive and time consuming task.
        This method caches the result for a period of time.
        """
        self.logger.info("Updating Company Profiles Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_COMPANIES)

        # If result is already cached, return it
        if cached_data is None:
            self.logger.info("Companies Profile data not found in cache. Calling DeGiro")
            # Otherwise, call the expensive method
            result = self.__update_company_profile(debug_json_files)

            # Cache the result for 1 hour (3600 seconds)
            cache.set(CACHE_KEY_UPDATE_COMPANIES, result, timeout=3600)

            return result

        return cached_data

    def __update_portfolio(self, debug_json_files: dict = None):
        """Update the Portfolio DB data."""
        product_ids = self.__get_product_ids()

        products_info = self.__get_products_info(product_ids)
        if debug_json_files and "products_info.json" in debug_json_files:
            save_to_json(products_info, debug_json_files["products_info.json"])

        self.__import_products_info(products_info)
        self.__import_products_quotation()

    def __update_company_profile(self, debug_json_files: dict = None):
        company_profiles = self.__get_company_profiles()
        if debug_json_files and "company_profiles.json" in debug_json_files:
            save_to_json(company_profiles, debug_json_files["company_profiles.json"])

        self.__import_company_profiles(company_profiles)

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

    def __import_cash_movements(self, cash_data: dict) -> None:
        """Store the cash movements into the DB."""

        if cash_data:
            for row in cash_data:
                try:
                    CashMovements.objects.update_or_create(
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
                            "order_id": row.get("orderId", None)
                        }
                    )
                except Exception as error:
                    self.logger.error(f"Cannot import row: {row}")
                    self.logger.error("Exception: ", error)

    def __transform_json(self, account_overview: dict) -> list[dict] | None:
        """Flattens the data from deGiro `get_account_overview`."""

        if account_overview["data"]:
            # Use pd.json_normalize to convert the JSON to a DataFrame
            df = pd.json_normalize(account_overview["data"]["cashMovements"], sep="_")
            # Fix id values format after Pandas
            for col in ["productId", "id", "exchangeRate", "orderId"]:
                if col in df:
                    df[col] = df[col].apply(
                        lambda x: None if (pd.isnull(x) or pd.isna(x)) else str(x).replace(".0", "")
                    )
            for col in ["change"]:
                if col in df:
                    df[col] = df[col].apply(lambda x: None if (pd.isnull(x) or pd.isna(x)) else str(x))

            # Set the index explicitly
            df.set_index("date", inplace=True)

            # Sort the DataFrame by the 'date' column
            df = df.sort_values(by="date")

            return df.reset_index().to_dict(orient="records")
        else:
            return None

    def __get_transaction_history(self, from_date: date) -> date:
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
                Transactions.objects.update_or_create(
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
                self.logger.error("Exception: ", error)

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
        """Store the products information into the DB."""

        for key in products_info:
            row = products_info[key]
            try:
                ProductInfo.objects.update_or_create(
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
                self.logger.error("Exception: ", error)

    def __import_products_quotation(self) -> None:
        product_growth = self.portfolio_data.calculate_product_growth()

        # Include Currencies in the Quotations
        start_date = DegiroConfig.default().start_date.strftime(LocalizationUtility.DATE_FORMAT)
        for currency in CurrencyFX.to_list():
            if currency not in product_growth:
                product_growth[currency] = {
                    "history": {}
                }
                product_growth[currency]["history"][start_date] = 1

        delete_keys = []
        for key in product_growth.keys():
            product = ProductInfoRepository.get_product_info_from_id(key)

            # FIXME: Code copied from dashboard._create_products_quotation()
            # If the product is NOT tradable, we shouldn't consider it for Growth
            # The 'tradable' attribute identifies old Stocks, like the ones that are
            # renamed for some reason, and it's not good enough to identify stocks
            # that are provided as dividends, for example.
            if "Non tradeable" in product["name"]:
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
            final_date = LocalizationUtility.format_date_from_date(date.today())
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
            if product_growth[key]["product"].get("vwdIdSecondary") is not None:
                issue_id = product_growth[key]["product"].get("vwdIdSecondary")
            else:
                issue_id = product_growth[key]["product"].get("vwdId")

            interval = product_growth[key]["quotation"]["interval"]
            quotes_dict = self.degiro_service.get_product_quotation(issue_id, interval)

            # Update the data ONLY if we get something back from DeGiro
            if quotes_dict:
                ProductQuotation.objects.update_or_create(id=int(key), defaults={
                    "interval": Interval.P1D,
                    "last_import": LocalizationUtility.now(),
                    "quotations": quotes_dict
                })

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
                - Path to the Json file that stores the company profiles
        ### Returns:
            None.
        """

        for key in company_profiles:
            try:
                CompanyProfile.objects.update_or_create(isin=key, defaults={"data": company_profiles[key]})
            except Exception as error:
                self.logger.error(f"Cannot import ISIN: {key}")
                self.logger.error("Exception: ", error)
