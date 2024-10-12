import logging

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.services.currency_converter_service import CurrencyConverterService
from degiro.services.degiro_service import DeGiroService
from degiro.utils.localization import LocalizationUtility


class PortfolioService:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")

    def __init__(
        self,
        degiro_service: DeGiroService,
    ):
        self.degiro_service = degiro_service
        self.currency_service = CurrencyConverterService()

    def get_portfolio(self) -> list[dict]:
        portfolio_transactions = self.__get_porfolio_products()

        products_ids = [row["productId"] for row in portfolio_transactions]
        products_info = self.__get_products_info(products_ids=products_ids)

        # Get user's base currency
        base_currency = LocalizationUtility.get_base_currency()

        products_config = self.__get_product_config()

        my_portfolio = []
        portfolio_total_value = 0.0

        for tmp in portfolio_transactions:
            info = products_info[tmp["productId"]]
            company_profile = CompanyProfileRepository.get_company_profile_raw(info["isin"])
            sector = "Unknown"
            industry = "Unknown"
            country = "Unknown"
            if company_profile.get("data"):
                sector = company_profile["data"]["sector"]
                industry = company_profile["data"]["industry"]
                country = company_profile["data"]["contacts"]["COUNTRY"]

            currency = info["currency"]
            price = ProductQuotationsRepository.get_product_price(tmp["productId"])
            if price == 0.0 and "closePrince" in info:
                self.logger.warning(f"No quotation found for product {tmp['productId']}, using closePrice")
                price = info["closePrice"]

            value = tmp["size"] * price
            break_even_price = tmp["breakEvenPrice"]

            is_open = tmp["size"] != 0.0 and tmp["value"] != 0.0
            unrealized_gain = (price - break_even_price) * tmp["size"]

            if currency != base_currency:
                base_currency_price = self.currency_service.convert(price, currency, base_currency)
                base_currency_value = self.currency_service.convert(value, currency, base_currency)
                base_currency_break_even_price = self.currency_service.convert(
                    break_even_price, currency, base_currency
                )
                unrealized_gain = (base_currency_price - base_currency_break_even_price) * tmp["size"]
            else:
                base_currency_price = price
                base_currency_value = value
                base_currency_break_even_price = break_even_price

            percentage_gain = unrealized_gain / (value - unrealized_gain) if value > 0 else 0.0

            portfolio_total_value += value

            exchange_id = info["exchangeId"]
            exchange_abbr = exchange_name = None

            if exchanges := products_config.get("exchanges"):
                exchange = next((ex for ex in exchanges if ex["id"] == int(exchange_id)), None)
                if exchange:
                    exchange_abbr = exchange["hiqAbbr"]
                    exchange_name = exchange["name"]

            my_portfolio.append(
                {
                    "name": info["name"],
                    "symbol": info["symbol"],
                    "sector": sector,
                    "industry": industry,
                    "category": info["category"],
                    "exchangeId": exchange_id,
                    **({"exchangeAbbr": exchange_abbr} if exchange_abbr is not None else {}),
                    "exchangeName": exchange_name,
                    "country": country,
                    "productType": info["productType"],
                    "shares": tmp["size"],
                    "productCurrency": currency,
                    "price": price,
                    "formattedPrice": LocalizationUtility.format_money_value(value=price, currency=currency),
                    **({"formattedBaseCurrencyPrice": LocalizationUtility.format_money_value(
                        value=base_currency_price, currency=base_currency
                    )} if base_currency_price is not None else {}),
                    "breakEvenPrice": break_even_price,
                    "formattedBreakEvenPrice": LocalizationUtility.format_money_value(
                        value=break_even_price, currency=currency
                    ),  # GAK: Average Purchase Price
                    **({"formattedBaseCurrencyBreakEvenPrice": LocalizationUtility.format_money_value(
                        value=base_currency_break_even_price, currency=base_currency
                    )} if base_currency_break_even_price is not None else {}),
                    "value": value,
                    "formattedValue": LocalizationUtility.format_money_value(value=value, currency_symbol=currency),
                    "baseCurrencyValue": base_currency_value,
                    **({"formattedBaseCurrencyValue": LocalizationUtility.format_money_value(
                        value=base_currency_value, currency=base_currency
                    )} if base_currency_value is not None else {}),
                    "isOpen": is_open,
                    "unrealizedGain": unrealized_gain,
                    "formattedUnrealizedGain": LocalizationUtility.format_money_value(
                        value=unrealized_gain, currency=base_currency
                    ),
                    "percentageGain": f"{percentage_gain:.2%}",
                    "logoUrl": f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                    "portfolioSize": 0.0,  # Calculated in the next loop
                    "formattedPortfolioSize": 0.0,  # Calculated in the next loop
                }
            )

        # Calculate Stock Portfolio Size
        for entry in my_portfolio:
            size = entry["value"] / portfolio_total_value
            entry["portfolioSize"] = size
            entry["formattedPortfolioSize"] = f"{size:.2%}"

        return sorted(my_portfolio, key=lambda k: k["symbol"])

    def get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            if entry["isOpen"]:
                portfolio_total_value += entry["baseCurrencyValue"]
                tmp_total_portfolio[entry["name"]] = entry["baseCurrencyValue"]

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

        tmp_total_portfolio["totalDepositWithdrawal"] = CashMovementsRepository.get_total_cash_deposits_raw()
        tmp_total_portfolio["totalCash"] = CashMovementsRepository.get_total_cash()

        # Try to get the data directly from DeGiro, so we get up-to-date values
        realtime_total_portfolio = self.__get_realtime_portfolio_total()
        if realtime_total_portfolio:
            tmp_total_portfolio = realtime_total_portfolio

        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency_symbol=base_currency_symbol,
            ),
            "totalCash": tmp_total_portfolio["totalCash"],
            "totalCash_formatted": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currency_symbol=base_currency_symbol,
            ),
            "currentValue": portfolio_total_value,
            "currentValue_formatted": LocalizationUtility.format_money_value(
                value=portfolio_total_value, currency_symbol=base_currency_symbol
            ),
            "totalROI": roi,
            "totalROI_formatted": "{:,.2f}%".format(roi),
            "totalDepositWithdrawal": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalDepositWithdrawal"],
                currency_symbol=base_currency_symbol,
            ),
        }

        return total_portfolio

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
