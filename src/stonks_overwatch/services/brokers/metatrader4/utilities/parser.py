from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger(__name__, "[METATRADER4|PARSER]")

# Constants
SECTION_CLOSED = "Closed Transactions:"
SECTION_OPEN = "Open Trades:"
SECTION_WORKING = "Working Orders:"
SECTION_SUMMARY = "Summary:"
SECTION_ACCOUNT = "Account:"

KEYWORD_BALANCE = "balance"
KEYWORD_CANCELLED = "cancelled"

COL_TICKET = "Ticket"
COL_OPEN_TIME = "Open Time"

CLOSED_HEADERS = [
    "Ticket",
    "Open Time",
    "Type",
    "Size",
    "Item",
    "Open Price",
    "S / L",
    "T / P",
    "Close Time",
    "Close Price",
    "Commission",
    "Taxes",
    "Swap",
    "Profit",
]

OPEN_HEADERS_MAP = {
    0: "Ticket",
    1: "Open Time",
    2: "Type",
    3: "Size",
    4: "Item",
    5: "Price",
    6: "S / L",
    7: "T / P",
    9: "Market Price",
    10: "Commission",
    11: "Taxes",
    12: "Swap",
    13: "Profit",
}

WORKING_HEADERS_MAP = {
    0: "Ticket",
    1: "Open Time",
    2: "Type",
    3: "Size",
    4: "Item",
    5: "Price",
    6: "S / L",
    7: "T / P",
    9: "Market Price",
    10: "Comment",
}


@dataclass
class ParseResult:
    metadata: Dict[str, Any]
    closed_transactions: List[Dict[str, Any]]
    open_trades: List[Dict[str, Any]]
    working_orders: List[Dict[str, Any]]
    summary: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def clean_text(text: str) -> str:
    """Clean text by removing non-breaking spaces and stripping whitespace."""
    return text.replace("\xa0", " ").strip()


def extract_row_data(row: Tag) -> List[str]:
    """Extract cleaned text list from a table row."""
    cells = row.find_all("td")
    if not cells:
        return []
    return [clean_text(c.get_text()) for c in cells]


def _parse_closed_transaction(row_data: List[str]) -> Dict[str, Any]:
    """Parse a single row of closed transaction."""
    transaction = {}

    # Standard Closed Transaction
    if len(row_data) == len(CLOSED_HEADERS):
        for i, header in enumerate(CLOSED_HEADERS):
            transaction[header] = row_data[i]

    # Balance / Deposit Row
    elif KEYWORD_BALANCE in row_data:
        if len(row_data) >= 5:
            # For balance rows, the 4th column (index 3) spans multiple columns (Size...Swap)
            # containing the description.
            transaction = {
                "Ticket": row_data[0],
                "Open Time": row_data[1],
                "Type": row_data[2],
                "Size": "",
                "Item": "",
                "Price": "",
                "S / L": "",
                "T / P": "",
                "Close Time": "",
                "Commission": "0.00",
                "Taxes": "0.00",
                "Swap": "0.00",
                "Profit": row_data[-1],
                "Description": row_data[3],
            }
        else:
            transaction = {"Type": KEYWORD_BALANCE, "Raw": row_data}

    # Cancelled Orders
    elif len(row_data) == 11 and KEYWORD_CANCELLED in row_data[-1]:
        # Parse first 10 columns against headers
        for i in range(10):
            if i < len(CLOSED_HEADERS):
                transaction[CLOSED_HEADERS[i]] = row_data[i]

        # Fill remainder
        transaction["Commission"] = "0.00"
        transaction["Taxes"] = "0.00"
        transaction["Swap"] = "0.00"
        transaction["Profit"] = KEYWORD_CANCELLED

    else:
        logger.debug(f"Unrecognized closed transaction row format: {row_data}")
        transaction = {"Raw": row_data}

    return transaction


def _parse_open_trade(row_data: List[str]) -> Dict[str, Any]:
    trade = {}
    for idx, header in OPEN_HEADERS_MAP.items():
        if idx < len(row_data):
            trade[header] = row_data[idx]
    return trade


def _parse_working_order(row_data: List[str]) -> Dict[str, Any]:
    order = {}
    for idx, header in WORKING_HEADERS_MAP.items():
        if idx < len(row_data):
            order[header] = row_data[idx]
    return order


def _detect_section(first_cell: str, current_section: Optional[str]) -> Optional[str]:
    """Detect if the row signals the start of a new section."""
    if SECTION_CLOSED in first_cell:
        return SECTION_CLOSED
    elif SECTION_OPEN in first_cell:
        return SECTION_OPEN
    elif SECTION_WORKING in first_cell:
        return SECTION_WORKING
    elif SECTION_SUMMARY in first_cell:
        return SECTION_SUMMARY
    return current_section


def _parse_summary_row(row_data: List[str], result: ParseResult) -> None:
    """Parse a summary row."""
    for i, cell_text in enumerate(row_data):
        if cell_text.endswith(":") and i + 1 < len(row_data):
            key = cell_text[:-1].strip()
            val = row_data[i + 1]
            if key and val and not val.endswith(":"):
                result.summary[key] = val


def _parse_row_content(row_data: List[str], result: ParseResult, current_section: Optional[str]) -> None:
    """Parse the content of a row based on the current section."""
    first_cell = row_data[0]

    if current_section == SECTION_CLOSED:
        if first_cell.isdigit():
            result.closed_transactions.append(_parse_closed_transaction(row_data))

    elif current_section == SECTION_OPEN:
        if first_cell.isdigit():
            result.open_trades.append(_parse_open_trade(row_data))

    elif current_section == SECTION_WORKING:
        if first_cell.isdigit():
            result.working_orders.append(_parse_working_order(row_data))

    elif current_section == SECTION_SUMMARY:
        _parse_summary_row(row_data, result)


def _process_row(row, result: ParseResult, current_section: Optional[str]) -> Optional[str]:
    """Process a single row and update result/section state."""
    row_data = extract_row_data(row)
    if not row_data:
        return current_section

    first_cell = row_data[0]

    # 1. Detect Metadata and Account Information
    if SECTION_ACCOUNT in first_cell:
        result.metadata["header_row"] = row_data
        # Extract Account and Currency from the row
        # Typical format: ["Account: 12345", "Currency: USD", ...]
        for _i, cell in enumerate(row_data):
            if "Account:" in cell:
                # Extract account number (everything after "Account:")
                account_value = cell.replace("Account:", "").strip()
                if account_value:
                    result.summary["Account"] = account_value
            elif "Currency:" in cell:
                # Extract currency (everything after "Currency:")
                currency_value = cell.replace("Currency:", "").strip()
                if currency_value:
                    result.summary["Currency"] = currency_value
        return current_section

    # 2. Detect Sections
    new_section = _detect_section(first_cell, current_section)
    if new_section != current_section:
        return new_section

    # 3. Skip Headers
    if COL_TICKET in row_data and COL_OPEN_TIME in row_data:
        return current_section

    # 4. Parse Based on Section
    _parse_row_content(row_data, result, current_section)

    return current_section


def parse_mt4_html(html_content: str) -> ParseResult:
    """Parse MT4 HTML content string and return structured data."""
    soup = BeautifulSoup(html_content, "html.parser")

    result = ParseResult(metadata={}, closed_transactions=[], open_trades=[], working_orders=[], summary={})

    rows = soup.find_all("tr")
    current_section = None

    for row in rows:
        current_section = _process_row(row, result, current_section)

    return result
