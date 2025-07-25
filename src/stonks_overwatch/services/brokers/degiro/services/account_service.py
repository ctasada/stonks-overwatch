from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.services.helper import is_non_tradeable_product
from stonks_overwatch.services.models import AccountOverview
from stonks_overwatch.utils.core.logger import StonksLogger


class AccountOverviewService(BaseService):
    logger = StonksLogger.get_logger("stonks_overwatch.account_overview_data", "[DEGIRO|ACCOUNT_OVERVIEW]")

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)

    def get_account_overview(self) -> List[AccountOverview]:
        self.logger.debug("Get Account Overview")
        # FETCH DATA
        account_overview = CashMovementsRepository.get_cash_movements_raw()

        products_ids = []
        for cash_movement in account_overview:
            if cash_movement["productId"] is not None:
                products_ids.append(cash_movement["productId"])

        products_info = self.__get_products_info(products_ids)

        overview = []
        for cash_movement in account_overview:
            stock_name = ""
            stock_symbol = ""
            description = cash_movement["description"]

            if cash_movement["productId"] is not None:
                info = products_info[int(cash_movement["productId"])]

                if is_non_tradeable_product(info):
                    # If the product is non-tradeable, we want to include the real product, if exists
                    info = self.__find_equivalent_tradeable_product(info, products_info)

                stock_name = info["name"]
                stock_symbol = info["symbol"]

            overview.append(
                AccountOverview(
                    datetime=cash_movement["date"],
                    value_datetime=cash_movement["valueDate"],
                    stock_name=stock_name,
                    stock_symbol=stock_symbol,
                    description=description,
                    type=cash_movement["type"],
                    currency=cash_movement["currency"],
                    change=cash_movement.get("change", 0.0),
                )
            )

        return overview

    def __get_products_info(self, products_ids: List[int]) -> dict:
        """Fetch product information for the given product IDs.

        This method retrieves product information from the ProductInfoRepository
        for the specified product IDs. It returns a dict containing
        product details with the productId as key
        """
        # Remove duplicates from the list
        products_ids = list(set(products_ids))

        products_info = ProductInfoRepository.get_products_info_raw(products_ids)
        non_tradeable_products = []
        for product in products_info.values():
            if is_non_tradeable_product(product):
                non_tradeable_products.append(product["symbol"].replace(".D", ""))

        # Retrieve the real product info for non-tradeable products
        if non_tradeable_products:
            non_tradeable_products_info = ProductInfoRepository.get_products_info_raw_by_symbol(non_tradeable_products)
            products_info = products_info | self.__filter_non_tradeable_products(non_tradeable_products_info)

        return products_info

    def __filter_non_tradeable_products(self, products: dict) -> dict:
        """Filter out non-tradeable products from the list of products."""
        return {k: v for k, v in products.items() if not is_non_tradeable_product(v)}

    def __find_equivalent_tradeable_product(self, product: dict, all_products: dict) -> dict:
        """Find the equivalent tradeable product for a non-tradeable product."""
        if not is_non_tradeable_product(product):
            return product

        # Remove the ".D" suffix to find the equivalent tradeable product
        tradeable_symbol = product["symbol"].replace(".D", "")
        for entry in all_products.values():
            if entry["symbol"] == tradeable_symbol and not is_non_tradeable_product(entry):
                return entry

        return product
