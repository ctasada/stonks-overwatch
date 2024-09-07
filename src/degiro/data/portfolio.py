import logging
from datetime import date

from currency_converter import CurrencyConverter
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest
from django.core.cache import cache, caches
from django.db import connection

from degiro.models import ProductInfo, ProductQuotation
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.utils.datetime import calculate_dates_in_interval, calculate_interval
from degiro.utils.db_utils import dictfetchall
from degiro.utils.debug import save_to_json
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class PortfolioData:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.product_info_repository = ProductInfoRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.product_quotation_repository = ProductQuotationsRepository()
        self.cash_movements_repository = CashMovementsRepository()

    def get_portfolio(self):
        self.update_portfolio()
        return self.__get_portfolio()

    def update_portfolio(self, debug_json_files: dict = None):
        """Updating the Portfolio is a expensive anc time consuming task.
        This method caches the result for a period of time.
        """
        cache_key = "portfolio_data_update_from_degiro"
        cached_data = cache.get(cache_key)

        # If result is already cached, return it
        if cached_data is None:
            print("Portfolio data not found in cache. Calling DeGiro")
            self.logger.info("Portfolio data not found in cache. Calling DeGiro")
            # Otherwise, call the expensive method
            result = self.__update_portfolio(debug_json_files)

            # Cache the result for 1 hour (3600 seconds)
            cache.set(cache_key, result, timeout=3600)

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

    def __get_portfolio(self):
        portfolio_transactions = self.__get_porfolio_products()

        products_ids = [row["productId"] for row in portfolio_transactions]
        products_info = self.__get_products_info(products_ids=products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
        base_currency = LocalizationUtility.get_base_currency()

        products_config = self.__get_product_config()

        my_portfolio = []
        portfolio_total_value = 0.0

        for tmp in portfolio_transactions:
            info = products_info[tmp["productId"]]
            company_profile = self.company_profile_repository.get_company_profile_raw(info["isin"])
            sector = "Unknown"
            industry = "Unknown"
            if company_profile.get("data"):
                sector = company_profile["data"]["sector"]
                industry = company_profile["data"]["industry"]

            currency = info["currency"]
            price = self.product_quotation_repository.get_product_price(tmp["productId"])
            value = tmp["size"] * price
            break_even_price = tmp["breakEvenPrice"]
            if currency != base_currency:
                price = self.currency_converter.convert(price, currency, base_currency)
                value = self.currency_converter.convert(value, currency, base_currency)
                break_even_price = self.currency_converter.convert(break_even_price, currency, base_currency)
                currency = base_currency

            formatted_price = LocalizationUtility.format_money_value(value=price, currency=currency)
            formatted_value = LocalizationUtility.format_money_value(value=value, currency_symbol=base_currency_symbol)
            formatted_break_even_price = LocalizationUtility.format_money_value(
                value=break_even_price, currency=currency
            )
            is_open = tmp["size"] != 0.0 and tmp["value"] != 0.0
            unrealized_gain = (price - break_even_price) * tmp["size"]
            formatted_unrealized_gain = LocalizationUtility.format_money_value(value=unrealized_gain, currency=currency)
            percentage_gain = 0.0
            if value > 0:
                percentage_gain = unrealized_gain / (value - unrealized_gain)

            portfolio_total_value += value

            exchange_abbr = None
            exchange_name = None
            exchange_id = info["exchangeId"]
            if "exchanges" in products_config and products_config["exchanges"]:
                for exchange in products_config["exchanges"]:
                    if exchange["id"] == int(exchange_id):
                        exchange_abbr = exchange["hiqAbbr"]
                        exchange_name = exchange["name"]
                        break

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
                    "shares": tmp["size"],
                    "price": price,
                    "productType": info["productType"],
                    "productCurrency": info["currency"],
                    "formattedPrice": formatted_price,
                    "breakEvenPrice": break_even_price,
                    "formattedBreakEvenPrice": formatted_break_even_price,  # GAK: Average Purchase Price
                    "value": value,
                    "formattedValue": formatted_value,
                    "isOpen": is_open,
                    "unrealizedGain": unrealized_gain,
                    "formattedUnrealizedGain": formatted_unrealized_gain,
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
            portfolio_total_value += entry["value"]
            tmp_total_portfolio[entry["name"]] = entry["value"]

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

        tmp_total_portfolio["totalDepositWithdrawal"] = self.cash_movements_repository.get_total_cash_deposits_raw()
        tmp_total_portfolio["totalCash"] = self.cash_movements_repository.get_total_cash()

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

    def __get_realtime_portfolio_total(self) -> dict:
        try:
            update = DeGiro.get_client().get_update(
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

    def __get_porfolio_products(self) -> dict:
        try:
            update = DeGiro.get_client().get_update(
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
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT product_id,
                        SUM(quantity) AS size,
                        SUM(total_plus_all_fees_in_base_currency) as total_plus_all_fees_in_base_currency,
                        ABS(SUM(total_plus_all_fees_in_base_currency) / SUM(quantity)) AS break_even_price
                    FROM degiro_transactions
                    GROUP BY product_id
                    HAVING SUM(quantity) > 0;
                    """
                )
                local_portfolio = dictfetchall(cursor)
                for entry in local_portfolio:
                    entry["value"] = 1.0 # FIXME
                return local_portfolio

    def __get_products_info(self, products_ids: list) -> dict:
        try:
            return DeGiro.get_products_info(products_ids)
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.product_info_repository.get_products_info_raw(products_ids)

    def __get_product_config(self) -> dict:
        try:
            products_config = DeGiro.get_client().get_products_config()

            return products_config
        except Exception:
            return {}

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

        return product_ids

    def __import_products_info(self, products_info: dict) -> None:
        """Store the products information into the DB."""

        for key in products_info:
            row = products_info[key]
            try:
                ProductInfo.objects.update_or_create(
                    id=int(row["id"]),
                    name=row["name"],
                    isin=row["isin"],
                    symbol=row["symbol"],
                    contract_size=row["contractSize"],
                    product_type=row["productType"],
                    product_type_id=row["productTypeId"],
                    tradable=row["tradable"],
                    category=row["category"],
                    currency=row["currency"],
                    active=row["active"],
                    exchange_id=row["exchangeId"],
                    only_eod_prices=row["onlyEodPrices"],
                    is_shortable=row.get("isShortable", False),
                    feed_quality=row.get("feedQuality"),
                    order_book_depth=row.get("orderBookDepth"),
                    vwd_identifier_type=row.get("vwdIdentifierType"),
                    vwd_id=row.get("vwdId"),
                    quality_switchable=row.get("qualitySwitchable"),
                    quality_switch_free=row.get("qualitySwitchFree"),
                    vwd_module_id=row.get("vwdModuleId"),
                    feed_quality_secondary=row.get("feedQualitySecondary"),
                    order_book_depth_secondary=row.get("orderBookDepthSecondary"),
                    vwd_identifier_type_secondary=row.get("vwdIdentifierTypeSecondary"),
                    vwd_id_secondary=row.get("vwdIdSecondary"),
                    quality_switchable_secondary=row.get("qualitySwitchableSecondary"),
                    quality_switch_free_secondary=row.get("qualitySwitchFreeSecondary"),
                    vwd_module_id_secondary=row.get("vwdModuleIdSecondary"),
                )
            except Exception as error:
                print(f"Cannot import row: {row}")
                print("Exception: ", error)

    def calculate_product_growth(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, product_id, quantity FROM degiro_transactions
                """
            )
            results = dictfetchall(cursor)

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

    def __import_products_quotation(self) -> None:
        """FIXME"""
        product_growth = self.calculate_product_growth()

        delete_keys = []
        for key in product_growth.keys():
            product = self.product_info_repository.get_product_info_from_id(key)

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
            product_growth[key]["quotation"]["interval"] = calculate_interval(start_date)

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
            quotes = DeGiro.get_product_quotation(issue_id, interval)
            dates = calculate_dates_in_interval(date.today(), interval)
            quotes_dict = {}
            for count, day in enumerate(dates):
                # Keep only the dates that are in the quotation range
                from_date = product_growth[key]["quotation"]["from_date"]
                to_date = product_growth[key]["quotation"]["to_date"]
                if (
                    day >= LocalizationUtility.convert_string_to_date(from_date)
                    and day <= LocalizationUtility.convert_string_to_date(to_date)
                ):
                    quotes_dict[LocalizationUtility.format_date_from_date(day)] = quotes[count]

            ProductQuotation.objects.update_or_create(id=int(key), defaults={"quotations": quotes_dict})


