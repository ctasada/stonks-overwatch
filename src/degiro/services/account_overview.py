import logging

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.utils.localization import LocalizationUtility


class AccountOverviewService:
    logger = logging.getLogger("stocks_portfolio.account_overview_data")

    def get_account_overview(self) -> list:
        # FETCH DATA
        account_overview = CashMovementsRepository.get_cash_movements_raw()

        products_ids = []
        for cash_movement in account_overview:
            if cash_movement["productId"] is not None:
                products_ids.append(cash_movement["productId"])

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

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
