import dataclasses
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypedDict

import pycountry
from iso10383 import MICEntry

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.domain.constants import ProductType, Sector


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
            return LocalizationUtility.format_money_value(value=self.change, currency=self.currency)
        return ""


class Country:
    def __init__(self, iso_code: str):
        if len(iso_code) == 2:
            self.iso_code = iso_code.upper()
            self.country = pycountry.countries.get(alpha_2=self.iso_code)
        else:
            # FIXME: Retrieving the first match. How do we handle if the match is not correct?
            self.country = pycountry.countries.search_fuzzy(Country.__clean_string(iso_code))[0]
            self.iso_code = self.country.alpha_2

    @staticmethod
    def __clean_string(input_string: str) -> str:
        # Remove anything between parentheses
        cleaned_string = re.sub(r"\(.*?\)", "", input_string)
        # Strip the string
        return cleaned_string.strip()

    def get_name(self) -> str:
        return self.country.name

    def get_flag(self) -> str:
        return self.country.flag


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


class DividendType(Enum):
    PAID = 0
    ANNOUNCED = 1
    FORECASTED = 2
    EX_DIVIDEND = 3


@dataclass
class Dividend:
    dividend_type: DividendType
    payment_date: datetime
    stock_name: str
    stock_symbol: str
    currency: str
    amount: float = 0.0
    taxes: float = 0.0
    # Only used for EX_DIVIDEND type
    payout_date: Optional[datetime] = None

    def formatted_name(self) -> str:
        return format_stock_name(self.stock_name)

    def payment_date_as_string(self) -> str:
        return LocalizationUtility.format_date_from_date(self.payment_date)

    def payment_time_as_string(self) -> str:
        return LocalizationUtility.format_time_from_date(self.payment_date)

    def payout_date_as_string(self) -> str:
        return LocalizationUtility.format_date_from_date(self.payout_date)

    def formated_net_amount(self) -> str:
        """Returns the formatted change in the dividend amount after taxes."""
        return LocalizationUtility.format_money_value(value=self.net_amount(), currency=self.currency)

    def formated_gross_amount(self) -> str:
        return LocalizationUtility.format_money_value(value=self.gross_amount(), currency=self.currency)

    def formated_taxes_amount(self) -> str:
        return LocalizationUtility.format_money_value(value=self.taxes, currency=self.currency)

    def is_paid(self) -> bool:
        return self.dividend_type == DividendType.PAID

    def is_announced(self) -> bool:
        return self.dividend_type == DividendType.ANNOUNCED

    def is_forecasted(self) -> bool:
        return self.dividend_type == DividendType.FORECASTED

    def is_ex_dividend(self) -> bool:
        return self.dividend_type == DividendType.EX_DIVIDEND

    def day(self) -> str:
        return LocalizationUtility.get_date_day(self.payment_date)

    def month_year(self) -> str:
        return LocalizationUtility.format_date_to_month_year(self.payment_date)

    def net_amount(self) -> float:
        """
        Returns the net amount after taxes.
        """
        return self.amount - self.taxes

    def gross_amount(self) -> float:
        """
        Returns the gross amount before taxes.
        """
        return self.amount

    def tooltip(self) -> str:
        match self.dividend_type:
            case DividendType.PAID:
                return f"Gross: {self.formated_gross_amount()} <br> Taxes: {self.formated_taxes_amount()}"
            case DividendType.ANNOUNCED:
                return f"Gross: {self.formated_gross_amount()} <br> Taxes: {self.formated_taxes_amount()}"
            case DividendType.FORECASTED:
                return f"Gross: {self.formated_gross_amount()} <br> Taxes: {self.formated_taxes_amount()}"
            case DividendType.EX_DIVIDEND:
                return f"Payout Date: {self.payout_date_as_string()}"
        return ""


class FeeType(Enum):
    """
    Enum representing different types of fees.
    """

    TRANSACTION = "Transaction"
    FINANCE_TRANSACTION_TAX = "Finance Transaction Tax"
    CONNECTION = "Connection"
    ADR_GDR = "ADR/GDR"

    def __str__(self):
        return self.value


@dataclass
class Fee:
    """
    Represents a fee charged by a broker.
    """

    # FIXME: date and time can be probably merged in a single field
    date: str
    time: str
    type: FeeType
    description: str
    fee_value: float
    currency: str

    def fee_formatted(self) -> str:
        """Format the fee value for display."""
        return LocalizationUtility.format_money_value(value=self.fee_value, currency=self.currency)

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dict and handle enum specifically
        result = asdict(self)
        result["fee_formatted"] = self.fee_formatted()
        return result


@dataclass
class PortfolioEntry:
    name: str = ""
    symbol: str = ""
    isin: str = ""
    sector: Sector = None
    industry: str = ""
    category: str = ""
    exchange: Optional[MICEntry] = None
    country: Optional[Country] = None
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
    product_type_share: float = 0.0

    @property
    def percentage_unrealized_gain(self) -> float:
        return (
            self.unrealized_gain / (self.value - self.unrealized_gain)
            if self.value > 0 and self.value != self.unrealized_gain
            else 0.0
        )

    @property
    def percentage_realized_gain(self) -> float:
        return self.realized_gain / self.total_costs if self.realized_gain != 0.0 and self.total_costs != 0.0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        # FIXME: The asdict does infinite recursion. Need to handle the country separately
        country_name = self.country.get_name() if self.country else "Unknown Country"
        self.country = None
        # Convert to dict and handle enum specifically
        result = asdict(self)
        result["country"] = country_name
        result["sector"] = self.sector.value if self.sector else ""
        del result["exchange"]
        result["exchange_acronym"] = self.get_exchange_acronym()
        result["exchange_name"] = self.get_exchange_name()
        result["name"] = self.formatted_name()
        result["shares"] = self.formatted_shares()
        result["product_type"] = self.product_type.value
        result["formatted_product_type_share"] = self.formatted_product_type_share
        result["formatted_break_even_price"] = self.formatted_break_even_price
        result["formatted_base_currency_break_even_price"] = self.formatted_base_currency_break_even_price
        result["formatted_price"] = self.formatted_price
        result["formatted_base_currency_price"] = self.formatted_base_currency_price
        result["formatted_value"] = self.formatted_value
        result["formatted_base_currency_value"] = self.formatted_base_currency_value
        result["formatted_unrealized_gain"] = self.formatted_unrealized_gain
        result["formatted_realized_gain"] = self.formatted_realized_gain
        result["formatted_percentage_unrealized_gain"] = self.formatted_percentage_unrealized_gain
        result["formatted_percentage_realized_gain"] = self.formatted_percentage_realized_gain

        if self.product_type == ProductType.CASH:
            result["category"] = ""
        return result

    def get_exchange_acronym(self) -> str:
        acronym = self.exchange.acronym if self.exchange else ""
        if not acronym:
            acronym = self.exchange.operating_mic.acronym if self.exchange and self.exchange.operating_mic else ""
        if not acronym:
            acronym = self.exchange.mic if self.exchange else ""

        return acronym

    def get_exchange_name(self) -> str:
        name = self.exchange.market_name if self.exchange else ""

        return name.title()

    def formatted_name(self) -> str:
        if self.product_type != ProductType.STOCK:
            return self.name
        return format_stock_name(self.name)

    def formatted_shares(self) -> str:
        if self.product_type == ProductType.CRYPTO:
            return f"{self.shares}"
        elif self.shares.is_integer():
            return f"{int(self.shares)}"
        return f"{self.shares:.2f}"

    def formatted_product_type_share(self) -> str:
        return f"{self.product_type_share:.2%}"

    def formatted_break_even_price(self) -> str:
        return LocalizationUtility.format_money_value(value=self.break_even_price, currency=self.product_currency)

    def formatted_base_currency_break_even_price(self) -> str:
        return LocalizationUtility.format_money_value(
            value=self.base_currency_break_even_price, currency=self.base_currency
        )

    def formatted_price(self) -> str:
        return LocalizationUtility.format_money_value(value=self.price, currency=self.product_currency)

    def formatted_base_currency_price(self) -> str:
        return LocalizationUtility.format_money_value(value=self.base_currency_price, currency=self.base_currency)

    def formatted_value(self) -> str:
        return LocalizationUtility.format_money_value(value=self.value, currency=self.product_currency)

    def formatted_base_currency_value(self) -> str:
        return LocalizationUtility.format_money_value(value=self.base_currency_value, currency=self.base_currency)

    def formatted_unrealized_gain(self) -> str:
        return LocalizationUtility.format_money_value(value=self.unrealized_gain, currency=self.base_currency)

    def formatted_realized_gain(self) -> str:
        return LocalizationUtility.format_money_value(value=self.realized_gain, currency=self.base_currency)

    def formatted_percentage_unrealized_gain(self) -> str:
        return f"{self.percentage_unrealized_gain:.2%}"

    def formatted_percentage_realized_gain(self) -> str:
        return f"{self.percentage_realized_gain:.2%}"


class PortfolioId(Enum):
    """Portfolio identifiers with UI metadata.

    This enum stores only UI-specific metadata (logo, stability flag).
    Display names and IDs are computed from BrokerName, making BrokerName
    the true single source of truth.

    The `ALL` value is a special portfolio ID used for aggregating data
    across all brokers in the UI.

    Architecture:
    - Stores: BrokerName (or None for ALL), logo path, stable flag
    - Computes: id (from BrokerName.value), long_name (from BrokerName.short_name)
    - Benefits: No duplication, type-safe, guaranteed consistency

    Example:
        >>> portfolio = PortfolioId.DEGIRO
        >>> portfolio.id  # "degiro" (computed from BrokerName)
        >>> portfolio.long_name  # "DEGIRO" (computed from BrokerName)
        >>> portfolio.broker_name  # BrokerName.DEGIRO (stored directly)
        >>>
        >>> # Convert from BrokerName
        >>> portfolio = PortfolioId.from_broker_name(BrokerName.DEGIRO)
    """

    # Store: (broker_or_none, logo_path, stable_flag)
    ALL = (None, "/static/stonks_overwatch.svg", True)
    DEGIRO = (BrokerName.DEGIRO, "/static/logos/degiro.svg", True)
    BITVAVO = (BrokerName.BITVAVO, "/static/logos/bitvavo.svg", False)
    IBKR = (BrokerName.IBKR, "/static/logos/ibkr.svg", False)

    def __init__(self, broker: Optional[BrokerName], logo: str, stable: bool = True):
        """
        Initialize a PortfolioId enum member.

        Args:
            broker: BrokerName enum (None for ALL portfolio)
            logo: Path to logo image
            stable: Whether this broker integration is stable (default: True)
        """
        self._broker = broker
        self.logo = logo
        self.stable = stable

    @property
    def id(self) -> str:
        """
        Compute ID from broker name.

        Returns:
            Broker identifier string (e.g., "degiro", "all")

        Example:
            >>> PortfolioId.DEGIRO.id
            'degiro'
            >>> PortfolioId.ALL.id
            'all'
        """
        return self._broker.value if self._broker else "all"

    @property
    def long_name(self) -> str:
        """
        Compute display name from BrokerName.

        Returns:
            Display name for UI (e.g., "DEGIRO", "Portfolios")

        Example:
            >>> PortfolioId.DEGIRO.long_name
            'DEGIRO'
            >>> PortfolioId.ALL.long_name
            'Portfolios'
        """
        return self._broker.short_name if self._broker else "Portfolios"

    @property
    def broker_name(self) -> Optional[BrokerName]:
        """
        Get the corresponding BrokerName enum, or None for ALL.

        Returns:
            BrokerName enum if this is a broker portfolio, None if this is ALL

        Example:
            >>> PortfolioId.DEGIRO.broker_name
            BrokerName.DEGIRO
            >>> PortfolioId.ALL.broker_name
            None
        """
        return self._broker

    @classmethod
    def from_broker_name(cls, broker: BrokerName) -> "PortfolioId":
        """
        Create PortfolioId from BrokerName.

        Args:
            broker: BrokerName enum value

        Returns:
            Corresponding PortfolioId

        Raises:
            ValueError: If no PortfolioId exists for the given BrokerName

        Example:
            >>> portfolio = PortfolioId.from_broker_name(BrokerName.DEGIRO)
            >>> portfolio == PortfolioId.DEGIRO
            True
        """
        return cls.from_id(broker.value)

    @classmethod
    def get_broker_portfolios(cls) -> list["PortfolioId"]:
        """
        Get all portfolio IDs that represent actual brokers (excludes ALL).

        Returns:
            List of PortfolioId values excluding ALL

        Example:
            >>> portfolios = PortfolioId.get_broker_portfolios()
            >>> PortfolioId.ALL in portfolios
            False
            >>> PortfolioId.DEGIRO in portfolios
            True
        """
        return [p for p in cls if p != cls.ALL]

    @classmethod
    def values(cls) -> list["PortfolioId"]:
        """
        Get all PortfolioId values including ALL.

        Returns:
            List of all PortfolioId enum members

        Example:
            >>> all_portfolios = PortfolioId.values()
            >>> len(all_portfolios) >= 4  # ALL + brokers
            True
        """
        return list(cls)

    @classmethod
    def from_id(cls, broker_id: str) -> "PortfolioId":
        """
        Get PortfolioId from string identifier.

        Args:
            broker_id: String identifier (e.g., "degiro", "bitvavo", "all")

        Returns:
            Matching PortfolioId, or ALL if not found

        Example:
            >>> PortfolioId.from_id("degiro")
            PortfolioId.DEGIRO
            >>> PortfolioId.from_id("invalid")
            PortfolioId.ALL
        """
        for portfolio in cls:
            if portfolio.id == broker_id:
                return portfolio
        return cls.ALL

    def to_dict(self) -> dict:
        """
        Convert PortfolioId to dictionary for serialization.

        Returns:
            Dictionary with id, name, logo, and stable fields

        Example:
            >>> PortfolioId.DEGIRO.to_dict()
            {'id': 'degiro', 'name': 'DEGIRO', 'logo': '/static/logos/degiro.svg', 'stable': True}
        """
        return {"id": self.id, "name": self.long_name, "logo": self.logo, "stable": self.stable}


@dataclass
class TotalPortfolio:
    base_currency: str
    total_pl: float
    total_cash: float
    current_value: float
    total_roi: float
    total_deposit_withdrawal: float

    @property
    def total_pl_formatted(self) -> str:
        return LocalizationUtility.format_money_value(value=self.total_pl, currency=self.base_currency)

    @property
    def total_cash_formatted(self) -> str:
        return LocalizationUtility.format_money_value(value=self.total_cash, currency=self.base_currency)

    @property
    def current_value_formatted(self) -> str:
        return LocalizationUtility.format_money_value(value=self.current_value, currency=self.base_currency)

    @property
    def total_roi_formatted(self) -> str:
        return "{:,.2f}%".format(self.total_roi)

    @property
    def total_deposit_withdrawal_formatted(self) -> str:
        return LocalizationUtility.format_money_value(value=self.total_deposit_withdrawal, currency=self.base_currency)


@dataclass
class Transaction:
    name: str
    symbol: str
    date: str
    time: str
    buy_sell: str
    transaction_type: str
    price: float
    currency: str
    quantity: float
    total: float
    total_currency: str
    total_in_base_currency: float
    base_currency: str
    fees: float
    fees_currency: str

    def __post_init__(self):
        """Round monetary values to 2 decimal places."""
        object.__setattr__(self, "price", round(self.price, 2))
        object.__setattr__(self, "total", round(self.total, 2))
        object.__setattr__(self, "total_in_base_currency", round(self.total_in_base_currency, 2))
        object.__setattr__(self, "fees", round(self.fees, 2))

    @property
    def formatted_price(self) -> str:
        return LocalizationUtility.format_money_value(value=self.price, currency=self.currency)

    @property
    def formatted_total(self) -> str:
        return LocalizationUtility.format_money_value(value=self.total, currency=self.total_currency)

    @property
    def formatted_total_in_base_currency(self) -> str:
        return LocalizationUtility.format_money_value(value=self.total_in_base_currency, currency=self.base_currency)

    @property
    def formatted_fees(self) -> str:
        return LocalizationUtility.format_money_value(value=self.fees, currency=self.fees_currency)


def dataclass_to_dict(obj) -> dict:
    """
    Convert a dataclass instance to a dictionary, including support for '@property' attributes
    :param obj:
    :return: dictionary representation of the dataclass instance
    """
    if not dataclasses.is_dataclass(obj):
        raise ValueError("Provided object is not a dataclass instance")

    result = dataclasses.asdict(obj)
    for attr in dir(obj):
        if isinstance(getattr(type(obj), attr, None), property):
            result[attr] = getattr(obj, attr)
    return result


def format_stock_name(name: str) -> str:
    words = name.split()
    special_cases = {"jpmorgan": "JPMorgan", "ishares": "iShares"}
    preserve = {"SA", "SA.", "SA-B", "UCITS", "ETF", "USD", "EUR"}
    preserve_lower_to_original = {p.lower(): p for p in preserve}
    capitalized_words = []

    for word in words:
        if word.lower() in preserve_lower_to_original:
            # Use the original case from preserve set
            capitalized_words.append(preserve_lower_to_original[word.lower()])
        elif word.lower() in special_cases:
            # Use special case formatting
            capitalized_words.append(special_cases[word.lower()])
        else:
            # Regular title case
            capitalized_words.append(word.title())

    return " ".join(capitalized_words)
