from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

from currency_converter import CurrencyConverter

import logging


class PortofolioIntegration:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )

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
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
        baseCurrency = LocalizationUtility.get_base_currency()

        myPortfolio = []

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
                breakEvenPrice = portfolio["breakEvenPrice"]
                if currency != baseCurrency:
                    price = self.currencyConverter.convert(
                        price, currency, baseCurrency
                    )
                    value = self.currencyConverter.convert(
                        value, currency, baseCurrency
                    )
                    breakEvenPrice = self.currencyConverter.convert(
                        breakEvenPrice, currency, baseCurrency
                    )
                    currency = baseCurrency

                formattedPrice = LocalizationUtility.format_money_value(
                    value=price, currency=currency
                )
                formattedValue = LocalizationUtility.format_money_value(
                    value=value, currencySymbol=baseCurrencySymbol
                )
                formattedBreakEvenPrice = LocalizationUtility.format_money_value(
                    value=breakEvenPrice, currency=currency
                )

                unrealizedGain = (price - breakEvenPrice) * portfolio["size"]
                formattedUnrealizedGain = LocalizationUtility.format_money_value(
                    value=unrealizedGain, currency=currency
                )

                myPortfolio.append(
                    dict(
                        name=info["name"],
                        symbol=info["symbol"],
                        sector=sector,
                        industry=industry,
                        shares=portfolio["size"],
                        price=price,
                        formattedPrice=formattedPrice,
                        breakEvenPrice=breakEvenPrice,
                        formattedBreakEvenPrice=formattedBreakEvenPrice,  # GAK: Average Purchase Price
                        value=portfolio["value"],
                        formattedValue=formattedValue,
                        isOpen=(portfolio["size"] != 0.0 and portfolio["value"] != 0.0),
                        unrealizedGain=unrealizedGain,
                        formattedUnrealizedGain=formattedUnrealizedGain,
                        logoUrl=f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                    )
                )

        return sorted(myPortfolio, key=lambda k: k["symbol"])

    def get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolioTotalValue = 0.0

        for equity in portfolio:
            portfolioTotalValue += equity["value"]

        # SETUP REQUEST
        update = DeGiro.get_client().get_update(
            request_list=[
                UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
            ],
            raw=True,
        )

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        # Portfolio has a weird structure, lets convert it here
        tmp_total_portfolio = {}
        for value in update["totalPortfolio"]["value"]:
            if value.get("value") is not None:
                tmp_total_portfolio[value["name"]] = value["value"]
        # Finish conversion
        roi = (
            portfolioTotalValue / tmp_total_portfolio["totalDepositWithdrawal"] - 1
        ) * 100
        total_profit_loss = portfolioTotalValue - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currencySymbol=baseCurrencySymbol,
            ),
            "totalCash": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currencySymbol=baseCurrencySymbol,
            ),
            "currentValue": LocalizationUtility.format_money_value(
                value=portfolioTotalValue, currencySymbol=baseCurrencySymbol
            ),
            "totalROI": roi,
            "totalROI_formatted": "{:,.2f}%".format(roi),
            "totalDepositWithdrawal": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalDepositWithdrawal"],
                currencySymbol=baseCurrencySymbol,
            ),
        }

        return total_portfolio

    def __get_company_profile(self, product_isin):
        company_profile = DeGiro.get_client().get_company_profile(
            product_isin=product_isin,
            raw=True,
        )

        return company_profile
