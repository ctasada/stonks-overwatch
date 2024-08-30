import logging

from currency_converter import CurrencyConverter
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class PortofolioIntegration:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def get_portfolio(self):
        # SETUP REQUEST
        update = DeGiro.get_client().get_update(
            request_list=[
                UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
            ],
            raw=True,
        )
        # self.logger.debug(json.dumps(update, indent = 4))

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for portfolio in update["portfolio"]["value"]:
            # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
            if portfolio["id"].isnumeric():
                products_ids.append(int(portfolio["id"]))

        products_info = DeGiro.get_products_info(products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
        base_currency = LocalizationUtility.get_base_currency()

        my_portfolio = []

        for tmp in update["portfolio"]["value"]:
            # Portfolio has a weird structure, lets convert it here
            portfolio = {}
            for value in tmp["value"]:
                if value.get("value") is not None:
                    portfolio[value["name"]] = value["value"]
            # Finish conversion
            if portfolio["id"].isnumeric():
                info = products_info[portfolio["id"]]
                company_profile = self.__get_company_profile(info["isin"])

                sector = "Unknown"
                industry = "Unknown"
                if company_profile.get("data"):
                    sector = company_profile["data"]["sector"]
                    industry = company_profile["data"]["industry"]

                currency = info["currency"]
                price = portfolio["price"]
                value = portfolio["value"]
                break_even_price = portfolio["breakEvenPrice"]
                if currency != base_currency:
                    price = self.currency_converter.convert(price, currency, base_currency)
                    value = self.currency_converter.convert(value, currency, base_currency)
                    break_even_price = self.currency_converter.convert(break_even_price, currency, base_currency)
                    currency = base_currency

                formatted_price = LocalizationUtility.format_money_value(value=price, currency=currency)
                formatted_value = LocalizationUtility.format_money_value(
                    value=value, currency_symbol=base_currency_symbol
                )
                formatted_break_even_price = LocalizationUtility.format_money_value(
                    value=break_even_price, currency=currency
                )

                unrealized_gain = (price - break_even_price) * portfolio["size"]
                formatted_unrealized_gain = LocalizationUtility.format_money_value(
                    value=unrealized_gain, currency=currency
                )

                my_portfolio.append(
                    {
                        "name": info["name"],
                        "symbol": info["symbol"],
                        "sector": sector,
                        "industry": industry,
                        "shares": portfolio["size"],
                        "price": price,
                        "formattedPrice": formatted_price,
                        "breakEvenPrice": break_even_price,
                        "formattedBreakEvenPrice": formatted_break_even_price,  # GAK: Average Purchase Price
                        "value": portfolio["value"],
                        "formattedValue": formatted_value,
                        "isOpen": (portfolio["size"] != 0.0 and portfolio["value"] != 0.0),
                        "unrealizedGain": unrealized_gain,
                        "formattedUnrealizedGain": formatted_unrealized_gain,
                        "logoUrl": f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                    }
                )

        return sorted(my_portfolio, key=lambda k: k["symbol"])

    def get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        for equity in portfolio:
            portfolio_total_value += equity["value"]

        # SETUP REQUEST
        update = DeGiro.get_client().get_update(
            request_list=[
                UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
            ],
            raw=True,
        )

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

        # Portfolio has a weird structure, lets convert it here
        tmp_total_portfolio = {}
        for value in update["totalPortfolio"]["value"]:
            if value.get("value") is not None:
                tmp_total_portfolio[value["name"]] = value["value"]
        # Finish conversion
        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency_symbol=base_currency_symbol,
            ),
            "totalCash": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currency_symbol=base_currency_symbol,
            ),
            "currentValue": LocalizationUtility.format_money_value(
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

    def __get_company_profile(self, product_isin):
        company_profile = DeGiro.get_client().get_company_profile(
            product_isin=product_isin,
            raw=True,
        )

        return company_profile
