import logging
from datetime import date

import pandas as pd
from degiro_connector.trading.models.account import OverviewRequest

from degiro.config.degiro_config import DegiroConfig
from degiro.models import CashMovements
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.utils.debug import save_to_json
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class AccountOverviewData:
    logger = logging.getLogger("stocks_portfolio.account_overview_data")

    def __init__(self):
        self.product_info_repository = ProductInfoRepository()
        self.cash_movements_repository = CashMovementsRepository()

    def get_account_overview(self):
        self.update_account()
        return self.__get_account_overview()

    def update_account(self, debug_json_files: dict = None):
        """Update the Account DB data. Only does it if the data is older than today."""
        today = date.today()
        last_movement = self.cash_movements_repository.get_last_movement()
        if last_movement is None:
            last_movement = DegiroConfig.default().start_date

        if last_movement < today:
            account_overview = self.__get_cash_movements(last_movement)
            if debug_json_files and "account.json" in debug_json_files:
                save_to_json(account_overview, debug_json_files["account.json"])

            transformed_data = self.__transform_json(account_overview)
            if debug_json_files and "account_transform.json" in debug_json_files:
                save_to_json(account_overview, debug_json_files["account_transform.json"])

            self.__import_cash_movements(transformed_data)

    def __get_account_overview(self) -> list:
        # FETCH DATA
        account_overview = self.cash_movements_repository.get_cash_movements_raw()

        products_ids = []
        for cash_movement in account_overview:
            if cash_movement["productId"] is not None:
                products_ids.append(cash_movement["productId"])

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = self.product_info_repository.get_products_info_raw(products_ids)

        overview = []
        for cash_movement in account_overview:
            stock_name = ""
            stock_symbol = ""
            if cash_movement["productId"] is not None:
                info = products_info[int(cash_movement["productId"])]
                stock_name = info["name"]
                stock_symbol = info["symbol"]

            formated_change = ""
            if cash_movement["change"] is not None:
                formated_change = LocalizationUtility.format_money_value(
                    value=cash_movement["change"], currency=cash_movement["currency"]
                )

            unsettled_cash = 0
            formated_unsettled_cash = ""
            formated_total_balance = ""
            total_balance = 0
            if "balance" in cash_movement:
                total_balance = cash_movement.get("balance").get("total")
                formated_total_balance = LocalizationUtility.format_money_value(
                    value=total_balance, currency=cash_movement["currency"]
                )
                unsettled_cash = cash_movement.get("balance").get("unsettledCash")
                formated_unsettled_cash = LocalizationUtility.format_money_value(
                    value=unsettled_cash, currency=cash_movement["currency"]
                )

            overview.append(
                {
                    "date": LocalizationUtility.format_date_from_date(cash_movement["date"]),
                    "time": LocalizationUtility.format_time_from_date(cash_movement["date"]),
                    "valueDate": LocalizationUtility.format_date_from_date(cash_movement["valueDate"]),
                    "valueTime": LocalizationUtility.format_time_from_date(cash_movement["valueDate"]),
                    "stockName": stock_name,
                    "stockSymbol": stock_symbol,
                    "description": cash_movement["description"],
                    "type": cash_movement["type"],
                    "typeStr": cash_movement["type"].replace("_", " ").title(),
                    "currency": cash_movement["currency"],
                    "change": cash_movement.get("change", ""),
                    "formatedChange": formated_change,
                    "totalBalance": total_balance,
                    "formatedTotalBalance": formated_total_balance,
                    # Seems that this value is the proper one for Dividends. Checking ...
                    "unsettledCash": unsettled_cash,
                    "formatedUnsettledCash": formated_unsettled_cash,
                }
            )

        return overview

    def __get_cash_movements(self, from_date: date) -> dict:
        """Import Account data from DeGiro. Uses the `get_account_overview` method.

        ### Parameters
            * from_date : date
                - Starting date to import the data
        ### Returns:
            account information
        """
        trading_api = DeGiro.get_client()

        request = OverviewRequest(from_date=from_date, to_date=date.today())

        # FETCH DATA
        account_overview = trading_api.get_account_overview(
            overview_request=request,
            raw=True,
        )

        return account_overview

    def __transform_json(self, account_overview: dict) -> dict:
        """Flattens the data from deGiro `get_account_overview`."""

        if account_overview["data"]:
            # Use pd.json_normalize to convert the JSON to a DataFrame
            df = pd.json_normalize(account_overview["data"]["cashMovements"], sep="_")
            # Fix id values format after Pandas
            for col in ["productId", "id", "change", "exchangeRate", "orderId"]:
                if col in df:
                    df[col] = df[col].apply(
                        lambda x: None if (pd.isnull(x) or pd.isna(x) ) else str(x).replace(".0", "")
                    )

            # Set the index explicitly
            df.set_index("date", inplace=True)

            # Sort the DataFrame by the 'date' column
            df = df.sort_values(by="date")

            return df.reset_index().to_dict(orient="records")
        else:
            return None

    def __conv(self, i):
        return i or None

    def __import_cash_movements(self, cash_data: dict) -> None:
        """Store the cash movements into the DB."""

        if cash_data:
            for row in cash_data:
                try:
                    CashMovements.objects.create(
                        date=LocalizationUtility.convert_string_to_datetime(row["date"]),
                        value_date=LocalizationUtility.convert_string_to_datetime(row["valueDate"]),
                        description=row["description"],
                        product_id=row.get("productId"),
                        currency=row["currency"],
                        type=row["type"],
                        change=self.__conv(row.get("change", None)),
                        balance_unsettled_cash=row.get("balance_unsettledCash", None),
                        balance_flatex_cash=row.get("balance_flatexCash", None),
                        balance_cash_fund=row.get("balance_cashFund", None),
                        balance_total=row.get("balance_total", None),
                        exchange_rate=self.__conv(row.get("exchangeRate", None)),
                        order_id=row.get("orderId", None),
                    )
                except Exception as error:
                    self.logger.error(f"Cannot import row: {row}")
                    self.logger.error("Exception: ", error)
