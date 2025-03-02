import datetime
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, TypedDict

import pycountry

from stonks_overwatch.utils.constants import ProductType, Sector
from stonks_overwatch.utils.localization import LocalizationUtility


@dataclass
class AccountOverview:
    datetime: datetime = None
    value_datetime: datetime = None
    stock_name: str = ""
    stock_symbol: str = ""
    description: str = ""
    type: str = ""
    currency: str = ""
    change: float = 0.0

    def date(self) -> str:
        return LocalizationUtility.format_date_from_date(self.datetime)

    def time(self) -> str:
        return LocalizationUtility.format_time_from_date(self.datetime)

    def value_date(self) -> str:
        return LocalizationUtility.format_date_from_date(self.value_datetime)

    def value_time(self) -> str:
        return LocalizationUtility.format_time_from_date(self.value_datetime)

    def type_str(self) -> str:
        return self.type.replace("_", " ").title()

    def formated_change(self) -> str:
        if self.change and self.change != 0.0:
            return LocalizationUtility.format_money_value(
                value=self.change, currency=self.currency
            )
        return ""

class Country:
    def __init__(self, iso_code: str):
        if len(iso_code) == 2:
            self.iso_code = iso_code.upper()
            self.country = pycountry.countries.get(alpha_2=self.iso_code)
        else:
            # FIXME: Retrieving the first match. How do we handle if the match is not correct?
            self.country = pycountry.countries.search_fuzzy(Country.__clean_string(iso_code))[0]

    @staticmethod
    def __clean_string(input_string: str) -> str:
        # Remove anything between parentheses
        cleaned_string = re.sub(r'\(.*?\)', '', input_string)
        # Strip the string
        return cleaned_string.strip()

    def get_name(self) -> str:
        if self.country:
            return self.country.name
        return "Unknown Country"

    def get_flag(self) -> str|None:
        if self.country:
            return self.country.flag
        return None

class DailyValue(TypedDict):
    x: str  # date
    y: float  # value

class DepositType(Enum):
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"

@dataclass
class Deposit:
    datetime: datetime
    type: DepositType
    change: float
    currency: str
    description: str

    def datetime_as_date(self) -> str:
        return self.datetime.strftime("%Y-%m-%d")

    def change_formatted(self) -> str:
        return LocalizationUtility.format_money_value(value=self.change, currency=self.currency)

@dataclass
class PortfolioEntry:
    name: str = ""
    symbol: str = ""
    sector: Sector = None
    industry: str = ""
    category: str = ""
    exchange_id: str = ""
    exchange_abbr: str = ""
    exchange_name: str = ""
    country: Country = None
    product_type: ProductType = None
    shares: float = 0.0
    product_currency: str = ""
    price: float = 0.0
    base_currency_price: float = 0.0
    base_currency: str = ""
    break_even_price: float = 0.0
    value: float = 0.0
    base_currency_value: float = 0.0
    base_currency_break_even_price: float = 0.0
    is_open: bool = False
    unrealized_gain: float = 0.0
    realized_gain: float = 0.0
    total_costs: float = 0.0
    portfolio_size: float = 0.0

    @property
    def percentage_unrealized_gain(self) -> float:
        return self.unrealized_gain / (self.value - self.unrealized_gain) \
            if self.value > 0 and self.value != self.unrealized_gain else 0.0

    @property
    def percentage_realized_gain(self) -> float:
        return self.realized_gain / self.total_costs \
            if self.realized_gain != 0.0 and self.total_costs != 0.0 else 0.0

    @property
    def symbol_url(self) -> str:
        if self.product_type == ProductType.CRYPTO:
            return f"https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/{self.symbol.lower()}.svg"
        else:
            # Keep track of alternatives as NVSTly
            # return f"https://raw.githubusercontent.com/nvstly/icons/main/ticker_icons/{symbol.upper()}.png"
            # https://img.stockanalysis.com/logos1/MC/IBE.png
            return f"https://logos.stockanalysis.com/{self.symbol.lower()}.svg"

    def to_dict(self) -> Dict[str, Any]:
        # FIXME: The asdict does infinite recursion. Need to handle the country separately
        country_name = self.country.get_name() if self.country else "Unknown Country"
        self.country = None
        # Convert to dict and handle enum specifically
        result = asdict(self)
        result['country'] = country_name
        result['sector'] = self.sector.value if self.sector else ""
        result['symbol_url'] = self.symbol_url
        result['product_type'] = self.product_type.value
        result['formatted_portfolio_size'] = self.formatted_portfolio_size
        result['formatted_break_even_price'] = self.formatted_break_even_price
        result['formatted_base_currency_break_even_price'] = self.formatted_base_currency_break_even_price
        result['formatted_price'] = self.formatted_price
        result['formatted_base_currency_price'] = self.formatted_base_currency_price
        result['formatted_value'] = self.formatted_value
        result['formatted_base_currency_value'] = self.formatted_base_currency_value
        result['formatted_unrealized_gain'] = self.formatted_unrealized_gain
        result['formatted_realized_gain'] = self.formatted_realized_gain
        result['formatted_percentage_unrealized_gain'] = self.formatted_percentage_unrealized_gain
        result['formatted_percentage_realized_gain'] = self.formatted_percentage_realized_gain

        if self.product_type == ProductType.CASH:
            result['category'] = ""
            result['exchange_abbr'] = ""
        return result

    def formatted_portfolio_size(self) -> str :
        return f"{self.portfolio_size:.2%}"

    def formatted_break_even_price(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.break_even_price, currency=self.product_currency
        )

    def formatted_base_currency_break_even_price(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.base_currency_break_even_price, currency=self.base_currency
        )

    def formatted_price(self) -> str:
        return LocalizationUtility.format_money_value(value=self.price, currency=self.product_currency)

    def formatted_base_currency_price(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.base_currency_price, currency=self.base_currency
        )

    def formatted_value(self) -> str:
        return LocalizationUtility.format_money_value(value=self.value, currency=self.product_currency)

    def formatted_base_currency_value(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.base_currency_value, currency=self.base_currency
        )

    def formatted_unrealized_gain(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.unrealized_gain, currency=self.base_currency
        )

    def formatted_realized_gain(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.realized_gain, currency=self.base_currency
        )

    def formatted_percentage_unrealized_gain(self) -> str:
        return f"{self.percentage_unrealized_gain:.2%}"

    def formatted_percentage_realized_gain(self) -> str:
        return f"{self.percentage_realized_gain:.2%}"


class PortfolioId(Enum):
    ALL = ("all", "Portfolios", "/static/logos/all-portfolio.svg")
    DEGIRO = ("degiro", "DeGiro", "/static/logos/degiro.svg")
    BITVAVO = ("bitvavo", "Bitvavo", "/static/logos/bitvavo.svg")

    def __init__(self, id: str, long_name: str, logo: str):
        self.id = id
        self.long_name = long_name
        self.logo = logo

    @classmethod
    def values(cls) -> list:
        return list(cls)

    @classmethod
    def from_id(cls, id: str):
        for portfolio in cls:
            if portfolio.id == id:
                return portfolio
        return cls.ALL

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.long_name,
            "logo": self.logo
        }

@dataclass
class TotalPortfolio:
    total_pl: float
    total_pl_formatted: str
    total_cash: float
    total_cash_formatted: str
    current_value: float
    current_value_formatted: str
    total_roi: float
    total_roi_formatted: str
    total_deposit_withdrawal: float
    total_deposit_withdrawal_formatted: str

@dataclass
class Transaction:
    name: str
    symbol: str
    date: str
    time: str
    buy_sell: str
    transaction_type: str
    price: str
    quantity: float
    total: str
    total_in_base_currency: str
    fees: str
