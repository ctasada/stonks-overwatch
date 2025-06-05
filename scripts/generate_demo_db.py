"""Imports all necessary data from DeGiro.

The script is used to update or re-create the DB with all the necessary data from DeGiro.

Usage:
    poetry run python ./scripts/generate_demo_db.py --help
"""
import logging
import os
import random
import sys
import textwrap
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import django
import pandas as pd
from degiro_connector.quotecast.models.chart import Interval
from django.core.management import call_command

from stonks_overwatch.services.degiro.constants import TransactionType
from stonks_overwatch.utils.datetime import DateTimeUtility
from stonks_overwatch.utils.localization import LocalizationUtility

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stonks_overwatch.settings')
os.environ["DEMO_MODE"] = "True"
django.setup()

# The import is defined here, so all the Django configuration can be executed
from stonks_overwatch.repositories.degiro.models import (  # noqa: E402
    DeGiroCashMovements,
    DeGiroCompanyProfile,
    DeGiroProductInfo,
    DeGiroProductQuotation,
    DeGiroTransactions,
)
from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository  # noqa: E402
from stonks_overwatch.services.degiro.currency_converter_service import CurrencyConverterService  # noqa: E402
from stonks_overwatch.services.degiro.degiro_service import DeGiroService  # noqa: E402
from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR, STONKS_OVERWATCH_DB_NAME, TIME_ZONE  # noqa: E402

LIST_OF_PRODUCTS = {
    "5462588": {
        "id": "5462588",
        "name": "Advanced Micro Devices Inc",
        "isin": "US0079031078",
        "symbol": "AMD",
        "productType": "STOCK",
        "currency": "USD",
    },
    "332111": {
        "id": "332111",
        "name": "Microsoft Corp",
        "isin": "US5949181045",
        "symbol": "MSFT",
        "productType": "STOCK",
        "currency": "USD",
    },
    "4587473": {
        "id": "4587473",
        "name": "Vanguard S&P 500 UCITS ETF USD",
        "isin": "IE00B3XXRP09",
        "symbol": "VUSA",
        "productType": "ETF",
        "currency": "EUR",
    },
    "1147582": {
        "id": "1147582",
        "name": "NVIDIA Corp",
        "isin": "US67066G1040",
        "symbol": "NVDA",
        "productType": "STOCK",
        "currency": "USD",
    },
    "331829": {
        "id": "331829",
        "name": "Coca-Cola",
        "isin": "US1912161007",
        "symbol": "KO",
        "productType": "STOCK",
        "currency": "USD",
    },
    # "18333971": {
    #     "id": "18333971",
    #     "name": "Palantir Technologies Inc",
    #     "isin": "US69608A1088",
    #     "symbol": "PLTR",
    #     "productType": "STOCK",
    #     "currency": "USD",
    # },
    "331824": {
        "id": "331824",
        "name": "JPMorgan Chase & Co",
        "isin": "US46625H1005",
        "symbol": "JPM",
        "productType": "STOCK",
        "currency": "USD",
    },
    "331868": {
        "id": "331868",
        "name": "Apple Inc",
        "isin": "US0378331005",
        "symbol": "AAPL",
        "productType": "STOCK",
        "currency": "USD",
    },
    "322171": {
        "id": "322171",
        "name": "Intel Corp",
        "isin": "US4581401001",
        "symbol": "INTC",
        "productType": "STOCK",
        "currency": "USD",
    },
    "331941": {
        "id": "331941",
        "name": "Johnson & Johnson",
        "isin": "US4781601046",
        "symbol": "JNJ",
        "productType": "STOCK",
        "currency": "USD",
    },
    "331986": {
        "id": "331986",
        "name": "Walt Disney",
        "isin": "US2546871060",
        "symbol": "DIS",
        "productType": "STOCK",
        "currency": "USD",
    }
}

CURRENCY_PRODUCT_LIST = {
    "705366": {
        "id": "EUR/USD",
        "name": "EUR/USD",
        "isin": "EURUSD......",
        "symbol": "EUR/USD",
        "productType": "CURRENCY",
        "currency": "USD",
    }
}

class DBDemoGenerator:
    """Class to generate a demo DB with random data."""

    def __init__(self):
        self.degiro_service = DeGiroService(force=True)
        self.currency_converter = CurrencyConverterService()
        # Products Configuration. Contains information about the products, such as exchanges, trading venues, etc.
        self.products_config = self.degiro_service.get_client().get_products_config()

    @staticmethod
    def update_random_time(date: datetime, max_hour: int = 22) -> datetime:
        random_hour = random.randint(9, max_hour)
        random_minute = random.randint(0, 59)
        random_second = random.randint(0, 59)

        return date.replace(hour=random_hour, minute=random_minute, second=random_second)

    def generate_random_transaction(self, date: datetime, balance: float) -> float:
        """Generate a random cash movement.

        Args:
            :param date: The date for the cash movement
            :param balance: The current balance

        Returns:
            balance: The new balance after the transaction
        """

        # Sample product IDs
        product_id = random.choice(list(LIST_OF_PRODUCTS.keys()))
        product = DeGiroProductInfo.objects.get(id=product_id)
        currency = product.currency

        # Generate random values
        # FIXME: Should randomly sell products. Only if already bought and we have enough balance
        buysell = "B" # Buy or Sell (B or S)

        trading_venue : str = ""
        for exchange in self.products_config["exchanges"]:
            if exchange["id"] == product.exchange_id:
                trading_venue = exchange["tradingVenue"]
                break

        # Calculate values
        quotations = ProductQuotationsRepository.get_product_quotations(product_id)

        value = quotations[date.strftime(LocalizationUtility.DATE_FORMAT)]
        change_in_base_currency = self.currency_converter.convert(
            amount=value,
            currency=currency,
            new_currency="EUR",
            fx_date=date.date()
        )
        max_quantity = int(abs(balance) // abs(change_in_base_currency))

        # We need more balance to buy this product
        if max_quantity < 1:
            return balance

        quantity = random.randint(1, max_quantity)
        change = value * quantity
        fees = -1.00 # Hardcoded fees for the transaction
        if buysell == "B":
            change = -change

        auto_fx_fee = 0
        exchange_rate = 0
        change_in_base_currency = change_in_base_currency * quantity
        if currency != "EUR":
            exchange_rate = self.currency_converter.convert(
                amount=1.0,
                currency=currency,
                new_currency="EUR",
                fx_date=date.date()
            )
            auto_fx_fee = -1.00 * exchange_rate

        transaction_date = self.update_random_time(date)

        self.update_dividends(product_id, quantity, transaction_date)

        last_transaction = DeGiroTransactions.objects.order_by('-id').first()
        DeGiroTransactions.objects.create(
            id=last_transaction.id + 1 if last_transaction else 1,
            product_id=product_id,
            date=transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            buysell=buysell,
            price=value,
            quantity=quantity,
            total=change,
            order_type_id=0,
            counter_party="MK",
            transfered="0",
            fx_rate=exchange_rate,
            nett_fx_rate=exchange_rate,
            gross_fx_rate=exchange_rate,
            auto_fx_fee_in_base_currency=auto_fx_fee,
            total_in_base_currency=change_in_base_currency,
            fee_in_base_currency=fees,
            total_fees_in_base_currency=fees + auto_fx_fee,
            total_plus_fee_in_base_currency=change_in_base_currency + fees,
            total_plus_all_fees_in_base_currency=change_in_base_currency + fees + auto_fx_fee,
            transaction_type_id=TransactionType.BUY_SELL.value,
            trading_venue=trading_venue,
            # executing_entity_id="4PQUHN3JPFGFNF3BB653"
        )

        description = "DEGIRO Transactiekosten en/of kosten van derden"

        movement_date = transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT)
        movement_value_date = self.update_random_time(transaction_date).strftime(LocalizationUtility.TIME_DATE_FORMAT)

        # Calculate balances
        balance_unsettled_cash = balance - change_in_base_currency
        balance_flatex = balance
        balance_cash_fund = []
        balance_total = balance_unsettled_cash

        order_id = f"ORD{random.randint(10000, 99999)}"

        if currency == "EUR":
            exchange_rate = None

        DeGiroCashMovements.objects.create(
            date=movement_date,
            value_date=movement_value_date,
            description=description,
            currency="EUR",
            type="FLATEX_CASH_SWEEP",
            balance_unsettled_cash=str(balance_unsettled_cash),
            balance_flatex_cash=str(balance_flatex),
            balance_cash_fund=str(balance_cash_fund),
            balance_total=str(balance_total),
            product_id=product_id,
            change=change_in_base_currency,
            exchange_rate=exchange_rate,
            order_id=order_id
        )

        return balance - change_in_base_currency

    def update_dividends(self, product_id: str, quantity: int, transaction_date: datetime) -> None:
        if "dividends" not in LIST_OF_PRODUCTS[product_id]:
            return

        dividends = LIST_OF_PRODUCTS[product_id]["dividends"]
        transaction_date = transaction_date.astimezone(ZoneInfo(TIME_ZONE))
        mask = dividends.index > transaction_date
        dividends.loc[mask, "stocks"] += quantity
        LIST_OF_PRODUCTS[product_id]["dividends"] = dividends

    def create_deposit(self, date: datetime, amount: float) -> None:
        """Create the initial deposit transaction.

        Args:
            date: The date for the initial deposit
            amount: The amount of the initial deposit

        Returns:
            DeGiroCashMovements: The initial deposit transaction
        """
        deposit_datetime = self.update_random_time(date, max_hour=9)

        DeGiroCashMovements.objects.create(
            date=deposit_datetime.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            value_date=deposit_datetime.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            description="iDEAL storting",
            currency="EUR",
            type="CASH_TRANSACTION",
            balance_unsettled_cash=str(amount),
            balance_flatex_cash="0",
            balance_cash_fund="0",
            balance_total=str(amount),
            product_id=None,
            change=amount,
            exchange_rate=None,
            order_id=None
        )

    def create_products_info(self, start_date: str) -> None:
        """Create the product info in the DB."""

        products_list = list(LIST_OF_PRODUCTS.keys()) + list(CURRENCY_PRODUCT_LIST.keys())
        products_info = self.degiro_service.get_products_info(products_list)
        for key in products_info:
            row = products_info[key]
            try:
                DeGiroProductInfo.objects.create(
                    id=int(row["id"]),
                    name= row["name"],
                    isin= row["isin"],
                    symbol= row["symbol"],
                    contract_size= row["contractSize"],
                    product_type= row["productType"],
                    product_type_id= row["productTypeId"],
                    tradable= row["tradable"],
                    category= row["category"],
                    currency= row["currency"],
                    active= row["active"],
                    exchange_id= row["exchangeId"],
                    only_eod_prices= row["onlyEodPrices"],
                    is_shortable= row.get("isShortable", False),
                    feed_quality= row.get("feedQuality"),
                    order_book_depth= row.get("orderBookDepth"),
                    vwd_identifier_type= row.get("vwdIdentifierType"),
                    vwd_id= row.get("vwdId"),
                    quality_switchable= row.get("qualitySwitchable"),
                    quality_switch_free= row.get("qualitySwitchFree"),
                    vwd_module_id= row.get("vwdModuleId"),
                    feed_quality_secondary= row.get("feedQualitySecondary"),
                    order_book_depth_secondary= row.get("orderBookDepthSecondary"),
                    vwd_identifier_type_secondary= row.get("vwdIdentifierTypeSecondary"),
                    vwd_id_secondary= row.get("vwdIdSecondary"),
                    quality_switchable_secondary= row.get("qualitySwitchableSecondary"),
                    quality_switch_free_secondary= row.get("qualitySwitchFreeSecondary"),
                    vwd_module_id_secondary= row.get("vwdModuleIdSecondary"),
                )
            except Exception as error:
                logging.error(f"Cannot import row: {row}")
                logging.error("Exception: ", error)

            # Get the product quotation
            symbol = row["symbol"]
            if row.get("vwdIdSecondary") is not None:
                issue_id = row.get("vwdIdSecondary")
            else:
                issue_id = row.get("vwdId")

            if issue_id is None:
                logging.info(f"Issue ID not found for '{symbol}'({key}): {row}")
                continue

            interval = DateTimeUtility.calculate_interval(start_date)
            quotes_dict = self.degiro_service.get_product_quotation(issue_id, interval, symbol)

            # Update the data ONLY if we get something back from DeGiro
            if quotes_dict:
                DeGiroProductQuotation.objects.update_or_create(id=int(key), defaults={
                    "interval": Interval.P1D,
                    "last_import": LocalizationUtility.now(),
                    "quotations": quotes_dict
                })
            else:
                logging.info(f"No quotes found for '{symbol}'({key}): {row}")

            # Get the company profile
            company_profile = self.degiro_service.get_client().get_company_profile(
                product_isin=row["isin"],
                raw=True,
            )
            DeGiroCompanyProfile.objects.update_or_create(isin=row["isin"], defaults={"data": company_profile})

    def create_transactions(
            self, start_date: datetime, num_transactions: int, balance: float, monthly_deposit: float
    ) -> None:
        end_date = datetime.now()
        # Calculate time delta between start and end date
        total_days = (end_date - start_date).days

        # Add initial deposit as first transaction
        self.create_deposit(start_date, balance)

        # Generate remaining transactions
        last_month = start_date.month
        for i in range(num_transactions):
            # Calculate a date between start_date and end_date
            days_to_add = (total_days * i) // (num_transactions - 1)
            transaction_date = start_date + timedelta(days=days_to_add)
            # If Saturday (5), add 2 days; if Sunday (6), add 1 day
            if transaction_date.weekday() == 5:
                transaction_date += timedelta(days=2)
            elif transaction_date.weekday() == 6:
                transaction_date += timedelta(days=1)

            # Add monthly deposit on the first of the month
            if transaction_date.month != last_month:
                first_of_month = transaction_date.replace(day=1)
                self.create_deposit(first_of_month, monthly_deposit)
                balance += monthly_deposit
                last_month = transaction_date.month

            # Generate a random cash movement
            balance = self.generate_random_transaction(transaction_date, balance)

        # Save all transactions
        logging.info(f"Created {num_transactions} cash movements")

    def init_dividends(self, start_date: str) -> None:
        from stonks_overwatch.services.yfinance.y_finance_client import YFinanceClient

        # Retrieve the list of products
        products_list = list(LIST_OF_PRODUCTS.keys())

        # Make sure 'start_date' is a Timestamp with the same tz as the index
        start_date = pd.Timestamp(start_date).tz_localize(tz=TIME_ZONE)

        # Retrieve the dividends for those products
        yfinance_client = YFinanceClient()
        for product_id in products_list:
            product_info = LIST_OF_PRODUCTS[product_id]
            dividends = yfinance_client.get_ticker(product_info["symbol"]).dividends

            # If there are no dividends, skip this product
            if dividends.empty:
                continue

            filtered_dividends = dividends[dividends.index > start_date]
            if filtered_dividends.empty:
                continue

            # Add a new column with the number of stocks
            df = filtered_dividends.to_frame(name="dividends")
            df["stocks"] = 0
            # Add the dividends to the product info
            LIST_OF_PRODUCTS[product_id]["dividends"] = df

    def create_dividend_payments(self):
        """Create dividend payments for the products with dividends."""
        for product_id, product_info in LIST_OF_PRODUCTS.items():
            if "dividends" not in product_info:
                continue

            dividends = product_info["dividends"]

            # Iterate through the dividends and create a cash movement for each
            for date, row in dividends.iterrows():
                if row["stocks"] <= 0:
                    continue

                amount = row["dividends"] * row["stocks"]
                description = "Dividendbelasting"
                DeGiroCashMovements.objects.create(
                    date=date.strftime(LocalizationUtility.TIME_DATE_FORMAT),
                    value_date=date.strftime(LocalizationUtility.TIME_DATE_FORMAT),
                    description=description,
                    currency=product_info["currency"],
                    type="FLATEX_CASH_SWEEP",
                    balance_unsettled_cash=str(amount),
                    balance_flatex_cash="0",
                    balance_cash_fund="0",
                    balance_total=str(amount),
                    product_id=product_id,
                    change=amount,
                    exchange_rate=None,
                    order_id=None
                )

    def generate(self, from_date: str, num_transactions: int, initial_deposit: float, monthly_deposit: float) -> None:
        # Parse start date
        start_date = datetime.strptime(from_date, LocalizationUtility.DATE_FORMAT)

        logging.info("Creating demo DB with random data ...")
        call_command("migrate")

        # Create ProductsInfo
        logging.info("Creating products info ...")
        self.create_products_info(from_date)
        self.init_dividends(from_date)

        # Generate transactions
        self.create_transactions(start_date, num_transactions, initial_deposit, monthly_deposit)

        self.create_dividend_payments()


def init() -> None:
    """Execute the necessary initializations for the scripts."""
    # Configure logging for the stonks_overwatch module
    stonks_overwatch_logger = logging.getLogger("stonks_overwatch")
    stonks_overwatch_logger.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the console handler
    _format = "%(levelname)s %(asctime)s %(module)s %(message)s"
    formatter = logging.Formatter(_format)
    console_handler.setFormatter(formatter)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format=_format)

def parse_args() -> Namespace:
    """Parse command line arguments.
    ### Returns:
        Namespace: Parsed arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        Creates a demo DB with random data.

        Supported brokers are:
            * DeGiro
        """)
    )

    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date for generating transactions (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--num-transactions",
        type=int,
        required=True,
        help="Number of transactions to generate",
    )

    parser.add_argument(
        "--initial-deposit",
        type=int,
        required=True,
        help="Initial deposit amount in EUR",
    )

    parser.add_argument(
        "--monthly-deposit",
        type=int,
        required=True,
        help="Monthly deposit in EUR",
    )


    return parser.parse_args()

def main():
    init()
    args = parse_args()

    if os.path.exists(Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME)):
        demo_db_path = Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME)
        logging.info(f"Deleting existing Demo DB: {demo_db_path}")
        os.remove(Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME))

    """Main function to run the script."""
    generator = DBDemoGenerator()
    generator.generate(args.start_date, args.num_transactions, args.initial_deposit, args.monthly_deposit)

if __name__ == "__main__":
    main()
