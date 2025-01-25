import datetime
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, TypedDict

from stonks_overwatch.utils.constants import ProductType
from stonks_overwatch.utils.localization import LocalizationUtility


@dataclass
class AccountOverview:
    date: str = ""
    time: str = ""
    value_date: str = ""
    value_time: str = ""
    stock_name: str = ""
    stock_symbol: str = ""
    description: str = ""
    type: str = ""
    type_str: str = ""
    currency: str = ""
    change: float = 0.0
    formated_change: str = ""
    total_balance: str = ""
    formated_total_balance: str = ""
    unsettled_cash: str = ""
    formated_unsettled_cash: str = ""

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
    sector: str = ""
    industry: str = ""
    category: str = ""
    exchange_id: str = ""
    exchange_abbr: str = ""
    exchange_name: str = ""
    country: str = ""
    product_type: ProductType = None
    shares: str = ""
    product_currency: str = ""
    price: float = 0.0
    formatted_price: str = ""
    formatted_base_currency_price: str = ""
    break_even_price: float = 0.0
    formatted_break_even_price: str = ""
    formatted_base_currency_break_even_price: str = ""
    value: float = 0.0
    formatted_value: str = ""
    base_currency_value: float = 0.0
    formatted_base_currency_value: str = ""
    is_open: bool = False
    unrealized_gain: float = 0.0
    formatted_unrealized_gain: str = ""
    percentage_unrealized_gain: str = ""
    realized_gain: float = 0.0
    formatted_realized_gain: str = ""
    percentage_realized_gain: str = ""
    symbol_url: str = ""
    portfolio_size: float = 0.0
    formatted_portfolio_size: str = ""

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dict and handle enum specifically
        result = asdict(self)
        result['product_type'] = self.product_type.value
        if self.product_type == ProductType.CASH:
            result['category'] = ""
            result['exchange_abbr'] = ""
        return result

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
