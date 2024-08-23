from django.db import connection
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility


# FIXME: If data cannot be found in the DB, the code should get it from DeGiro, updating the DB
class AccountOverviewData:

    def get_account_overview(self):
        # FETCH DATA
        account_overview = self.__get_cash_movements()

        products_ids = []
        for cash_movement in account_overview:
            if cash_movement["productId"] is not None:
                products_ids.append(cash_movement["productId"])

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = self.__getProductsInfo(products_ids)

        overview = []
        for cash_movement in account_overview:

            stockName = ""
            stockSymbol = ""
            if cash_movement["productId"] is not None:
                info = products_info[int(cash_movement["productId"])]
                stockName = info["name"]
                stockSymbol = info["symbol"]

            formatedChange = ""
            if cash_movement["change"] is not None:
                formatedChange = LocalizationUtility.format_money_value(
                    value=cash_movement["change"], currency=cash_movement["currency"]
                )

            unsettledCash = 0
            formatedUnsettledCash = ""
            formatedTotalBalance = ""
            totalBalance = 0
            if "balance" in cash_movement:
                totalBalance = cash_movement.get("balance").get("total")
                formatedTotalBalance = LocalizationUtility.format_money_value(
                    value=totalBalance, currency=cash_movement["currency"]
                )
                unsettledCash = cash_movement.get("balance").get("unsettledCash")
                formatedUnsettledCash = LocalizationUtility.format_money_value(
                    value=unsettledCash, currency=cash_movement["currency"]
                )

            overview.append(
                dict(
                    date=LocalizationUtility.format_date_from_date(cash_movement["date"]),
                    time=LocalizationUtility.format_time_from_date(cash_movement["date"]),
                    valueDate=LocalizationUtility.format_date_from_date(cash_movement["valueDate"]),
                    valueTime=LocalizationUtility.format_time_from_date(cash_movement["valueDate"]),
                    stockName=stockName,
                    stockSymbol=stockSymbol,
                    description=cash_movement["description"],
                    type=cash_movement["type"],
                    typeStr=cash_movement["type"].replace("_", " ").title(),
                    currency=cash_movement["currency"],
                    change=cash_movement.get("change", ""),
                    formatedChange=formatedChange,
                    totalBalance=totalBalance,
                    formatedTotalBalance=formatedTotalBalance,
                    # Seems that this value is the proper one for Dividends. Checking ...
                    unsettledCash=unsettledCash,
                    formatedUnsettledCash=formatedUnsettledCash,
                )
            )

        return overview

    def get_dividends(self):
        overview = self.get_account_overview()

        dividends = []
        for transaction in overview:
            # We don't include 'Dividendbelasting' because the 'value' seems to already include the taxes
            if transaction["description"] in [
                "Dividend",
                "Dividendbelasting",
                "Vermogenswinst",
            ]:
                dividends.append(transaction)

        return dividends

    def __get_cash_movements(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_cashmovements
                ORDER BY date DESC
                """
            )
            return dictfetchall(cursor)

    # FIXME: Duplicated code
    def __getProductsInfo(self, ids):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE id IN ({", ".join(map(str, ids))})
                """
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row['id']: row for row in rows}
        return result_map
