import logging
from typing import List

from stonks_overwatch.repositories.degiro.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.repositories.degiro.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.models import AccountOverview


class AccountOverviewService:
    logger = logging.getLogger("stocks_portfolio.account_overview_data")

    def get_account_overview(self) -> List[AccountOverview]:
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

            overview.append(
                AccountOverview(
                    datetime=cash_movement["date"],
                    value_datetime=cash_movement["valueDate"],
                    stock_name=stock_name,
                    stock_symbol=stock_symbol,
                    description=cash_movement["description"],
                    type=cash_movement["type"],
                    currency=cash_movement["currency"],
                    change=cash_movement.get("change", 0.0),
                )
            )

        return overview
