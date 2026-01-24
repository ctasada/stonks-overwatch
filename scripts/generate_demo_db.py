"""Imports all necessary data from DeGiro.

The script is used to update or re-create the DB with all the necessary data from DeGiro.

Usage:
    poetry run python -m scripts.generate_demo_db --help
"""

import logging
import os
import random
import shutil
import textwrap
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.common import setup_script_environment

# Set up Django environment and logging - with demo mode
os.environ["DEMO_MODE"] = "True"
setup_script_environment()

# Import Django and application modules after setup
from degiro_connector.quotecast.models.chart import Interval  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connections  # noqa: E402

from stonks_overwatch.constants import BrokerName  # noqa: E402
from stonks_overwatch.services.brokers.degiro.client.constants import TransactionType  # noqa: E402

# The import is defined here, so all the Django configuration can be executed
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService  # noqa: E402
from stonks_overwatch.services.brokers.degiro.repositories.models import (  # noqa: E402
    DeGiroCashMovements,
    DeGiroCompanyProfile,
    DeGiroProductInfo,
    DeGiroProductQuotation,
    DeGiroTransactions,
)
from stonks_overwatch.services.brokers.degiro.repositories.product_quotations_repository import (  # noqa: E402
    ProductQuotationsRepository,
)
from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService  # noqa: E402
from stonks_overwatch.settings import DATABASES, TIME_ZONE  # noqa: E402
from stonks_overwatch.utils.core.datetime import DateTimeUtility  # noqa: E402
from stonks_overwatch.utils.core.localization import LocalizationUtility  # noqa: E402

LIST_OF_PRODUCTS = {
    # "5462588": {
    #     "id": "5462588",
    #     "name": "Advanced Micro Devices Inc",
    #     "isin": "US0079031078",
    #     "symbol": "AMD",
    #     "productType": "STOCK",
    #     "currency": "USD",
    # },
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
    # Splits are not yet supported by the Demo Generation
    # "1147582": {
    #     "id": "1147582",
    #     "name": "NVIDIA Corp",
    #     "isin": "US67066G1040",
    #     "symbol": "NVDA",
    #     "productType": "STOCK",
    #     "currency": "USD",
    # },
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
    },
    "102143113": {
        "id": "102143113",
        "name": "Bitcoin",
        "isin": "XFC000A2YY6Q",
        "symbol": "BTC",
        "productType": "CRYPTO",
        "currency": "EUR",
        "decimals": 8,
    },
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
        # Ensure the DeGiro service is connected before using it
        if not self.degiro_service.is_connected():
            self.degiro_service.connect()
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
        supported_decimals = LIST_OF_PRODUCTS[product_id].get("decimals", 0)
        product = DeGiroProductInfo.objects.get(id=product_id)
        currency = product.currency

        # Generate random values
        # FIXME: Should randomly sell products. Only if already bought and we have enough balance
        buysell = "B"  # Buy or Sell (B or S)

        trading_venue: str = ""
        for exchange in self.products_config["exchanges"]:
            if exchange["id"] == product.exchange_id:
                trading_venue = exchange["tradingVenue"]
                break

        # Calculate values
        quotations = ProductQuotationsRepository.get_product_quotations(product_id)

        value = quotations[date.strftime(LocalizationUtility.DATE_FORMAT)]
        change_in_base_currency = self.currency_converter.convert(
            amount=value, currency=currency, new_currency="EUR", fx_date=date.date()
        )
        max_quantity = abs(balance) / abs(change_in_base_currency)

        # We need more balance to buy this product
        if max_quantity < 1 and supported_decimals == 0:
            return balance

        if supported_decimals > 0:
            # Choose a random float between a small minimum and max_quantity, with correct precision
            min_quantity = 10 ** (-supported_decimals)
            # Ensure max_quantity is at least min_quantity to avoid ValueError in random.uniform
            if max_quantity < min_quantity:
                return balance
            quantity = round(random.uniform(min_quantity, max_quantity), supported_decimals)
        else:
            quantity = random.randint(1, int(max_quantity))

        change = value * quantity
        fees = -1.00  # FIXME: Hardcoded fees for the transaction
        if buysell == "B":
            change = -change

        auto_fx_fee = 0
        exchange_rate = 0
        change_in_base_currency = change_in_base_currency * quantity
        if currency != "EUR":
            exchange_rate = self.currency_converter.convert(
                amount=1.0, currency=currency, new_currency="EUR", fx_date=date.date()
            )
            auto_fx_fee = -1.00 * exchange_rate

        transaction_date = self.update_random_time(date)
        movement_date = transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT)

        self.update_dividends(product_id, quantity, transaction_date)

        last_transaction = DeGiroTransactions.objects.order_by("-id").first()
        DeGiroTransactions.objects.create(
            id=last_transaction.id + 1 if last_transaction else 1,
            product_id=product_id,
            date=movement_date,
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
        )

        movement_value_date = self.update_random_time(transaction_date).strftime(LocalizationUtility.TIME_DATE_FORMAT)

        order_id = f"ORD{random.randint(10000, 99999)}"

        description = f"Koop {quantity} @ {value} {currency}"
        balance_total = balance - abs(change)

        DeGiroCashMovements.objects.create(
            date=movement_date,
            value_date=movement_value_date,
            description=description,
            currency=currency,
            type="TRANSACTION",
            balance_unsettled_cash=str(round(change, 2)),
            balance_flatex_cash=str(round(balance, 2)),
            balance_total=str(round(balance_total, 2)),
            product_id=product_id,
            change=round(change_in_base_currency, 2),
            exchange_rate=exchange_rate,
            order_id=order_id,
        )

        description = "DEGIRO Transactiekosten en/of kosten van derden"

        # Calculate balances
        balance_unsettled_cash = round(balance - change_in_base_currency, 2)
        balance_flatex = round(balance, 2)
        balance_cash_fund = []
        balance_total = balance_unsettled_cash

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
            change=round(change_in_base_currency, 2),
            exchange_rate=exchange_rate,
            order_id=order_id,
        )

        return balance - change_in_base_currency

    def update_dividends(self, product_id: str, quantity: int | float, transaction_date: datetime) -> None:
        """Update dividend tracking for a product after a purchase.

        Args:
            product_id: The product identifier
            quantity: Number of shares/units purchased (can be float for crypto)
            transaction_date: When the purchase was made
        """
        if "dividends" not in LIST_OF_PRODUCTS[product_id]:
            return

        dividends = LIST_OF_PRODUCTS[product_id]["dividends"]
        transaction_date = transaction_date.astimezone(ZoneInfo(TIME_ZONE))
        mask = dividends.index > transaction_date
        dividends.loc[mask, "stocks"] += quantity
        LIST_OF_PRODUCTS[product_id]["dividends"] = dividends

    def create_deposit(self, date: datetime, deposit: float, balance: float) -> None:
        """Create the initial deposit transaction.

        Args:
            date: The date for the deposit
            deposit: The amount to deposit
            balance: The current balance

        Returns:
            DeGiroCashMovements: The deposit transaction
        """
        deposit_datetime = self.update_random_time(date, max_hour=9)
        total_balance = round(balance + deposit, 2)

        DeGiroCashMovements.objects.create(
            date=deposit_datetime.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            value_date=deposit_datetime.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            description="iDEAL storting",
            currency="EUR",
            type="CASH_TRANSACTION",
            balance_unsettled_cash=str(deposit),
            balance_flatex_cash="0",
            balance_cash_fund="0",
            balance_total=str(total_balance),
            product_id=None,
            change=deposit,
            exchange_rate=None,
            order_id=None,
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
                logging.error(f"Cannot import row: {row}")
                logging.error(f"Exception: {error}", exc_info=True)

            # Get the product quotation
            symbol = row["symbol"]

            interval = DateTimeUtility.calculate_interval(start_date)
            identifier_type = row.get("vwdIdentifierTypeSecondary")
            identifier_value = row.get("vwdIdSecondary")
            if identifier_type is None:
                identifier_type = row.get("vwdIdentifierType")
                identifier_value = row.get("vwdId")

            # Skip if no valid identifier is available
            if identifier_value is None:
                logging.info(f"No valid identifier for '{symbol}'({key}): {row}")
                continue

            quotes_dict = self.degiro_service.get_product_quotation(identifier_type, identifier_value, interval, symbol)

            # Update the data ONLY if we get something back from DeGiro
            if quotes_dict:
                filtered_quotes = {
                    k: v
                    for k, v in quotes_dict.items()
                    if datetime.strptime(k, LocalizationUtility.DATE_FORMAT)
                    >= datetime.strptime(start_date, LocalizationUtility.DATE_FORMAT)
                }

                DeGiroProductQuotation.objects.update_or_create(
                    id=int(key),
                    defaults={
                        "interval": Interval.P1D,
                        "last_import": LocalizationUtility.now(),
                        "quotations": filtered_quotes,
                    },
                )
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

            if transaction_date > datetime.now():
                transaction_date = datetime.now()
                if transaction_date.weekday() == 5:
                    transaction_date -= timedelta(days=1)
                elif transaction_date.weekday() == 6:
                    transaction_date -= timedelta(days=2)

            # Add monthly deposit on the first of the month
            if transaction_date.month != last_month:
                first_of_month = transaction_date.replace(day=1)
                self.create_deposit(first_of_month, monthly_deposit, balance)
                balance += monthly_deposit
                last_month = transaction_date.month

            # Generate a random cash movement
            balance = self.generate_random_transaction(transaction_date, balance)

        # Save all transactions
        logging.info(f"Created {num_transactions} cash movements")

    def init_dividends(self, start_date: str) -> None:
        from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import YFinanceClient

        # Retrieve the list of products
        products_list = list(LIST_OF_PRODUCTS.keys())

        # Make sure 'start_date' is a datetime with the same tz as the index
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=ZoneInfo(TIME_ZONE))

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
                    order_id=None,
                )

    def enable_broker(self, broker_name: BrokerName) -> None:
        """Enable a broker in the BrokersConfiguration table.

        Args:
            broker_name: Name of the broker to enable
        """
        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        logging.info(f"Enabling broker: {broker_name}")
        try:
            broker_config = BrokersConfiguration.objects.using("demo").get(broker_name=broker_name)
            broker_config.enabled = True
            broker_config.save(using="demo")
            logging.info(f"Successfully enabled {broker_name}")
        except BrokersConfiguration.DoesNotExist:
            logging.warning(f"BrokersConfiguration for {broker_name} does not exist - will be created by migrations")

    def update_quotations(self) -> None:
        """Update quotations for all products in the existing demo database."""
        logging.info("Updating quotations for existing demo database...")

        # Get all existing products from the database
        products = DeGiroProductInfo.objects.using("demo").all()

        if not products.exists():
            logging.warning("No products found in demo database. Nothing to update.")
            return

        # Get the earliest transaction date to determine the start date for quotations
        earliest_transaction = DeGiroTransactions.objects.using("demo").order_by("date").first()
        if earliest_transaction:
            start_date = earliest_transaction.date.strftime(LocalizationUtility.DATE_FORMAT)
            logging.info(f"Earliest transaction date: {start_date}")
        else:
            # If no transactions, use a default start date (e.g., 1 year ago)
            start_date = (datetime.now() - timedelta(days=365)).strftime(LocalizationUtility.DATE_FORMAT)
            logging.info(f"No transactions found, using default start date: {start_date}")

        interval = DateTimeUtility.calculate_interval(start_date)
        updated_count = 0
        skipped_count = 0

        for product in products:
            symbol = product.symbol
            product_id = str(product.id)

            # Determine which identifier to use
            identifier_type = product.vwd_identifier_type_secondary
            identifier_value = product.vwd_id_secondary
            if identifier_type is None:
                identifier_type = product.vwd_identifier_type
                identifier_value = product.vwd_id

            # Skip if no valid identifier is available
            if identifier_value is None:
                logging.warning(f"No valid identifier for '{symbol}' (ID: {product_id}), skipping")
                skipped_count += 1
                continue

            try:
                logging.info(f"Updating quotations for '{symbol}' (ID: {product_id})...")
                quotes_dict = self.degiro_service.get_product_quotation(
                    identifier_type, identifier_value, interval, symbol
                )

                # Update the data ONLY if we get something back from DeGiro
                if quotes_dict:
                    # Filter quotes to only include dates after start_date
                    filtered_quotes = {
                        k: v
                        for k, v in quotes_dict.items()
                        if datetime.strptime(k, LocalizationUtility.DATE_FORMAT)
                        >= datetime.strptime(start_date, LocalizationUtility.DATE_FORMAT)
                    }

                    DeGiroProductQuotation.objects.using("demo").update_or_create(
                        id=int(product_id),
                        defaults={
                            "interval": Interval.P1D,
                            "last_import": LocalizationUtility.now(),
                            "quotations": filtered_quotes,
                        },
                    )
                    updated_count += 1
                    logging.info(f"  ✓ Updated {len(filtered_quotes)} quotations for '{symbol}'")
                else:
                    logging.warning(f"  ✗ No quotes found for '{symbol}' (ID: {product_id})")
                    skipped_count += 1

            except Exception as e:
                logging.error(f"  ✗ Error updating quotations for '{symbol}' (ID: {product_id}): {e}")
                skipped_count += 1

        logging.info(f"Quotation update complete: {updated_count} updated, {skipped_count} skipped")

    def generate(self, from_date: str, num_transactions: int, initial_deposit: float, monthly_deposit: float) -> None:
        # Parse start date
        start_date = datetime.strptime(from_date, LocalizationUtility.DATE_FORMAT)

        logging.info("Creating demo DB with random data ...")
        call_command("migrate", database="demo")

        # Enable DEGIRO broker
        self.enable_broker(BrokerName.DEGIRO)

        # Create ProductsInfo
        logging.info("Creating products info ...")
        self.create_products_info(from_date)
        self.init_dividends(from_date)

        # Add initial deposit as first transaction
        self.create_deposit(start_date, initial_deposit, 0.0)

        # Generate transactions
        self.create_transactions(start_date, num_transactions, initial_deposit, monthly_deposit)

        self.create_dividend_payments()


def parse_args() -> Namespace:
    """Parse command line arguments.
    ### Returns:
        Namespace: Parsed arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        Creates or updates a demo DB with random data.

        Supported brokers are:
            * DeGiro

        Modes:
            1. Create mode (default): Creates a new demo database from scratch
            2. Update mode (--update): Updates quotations in existing demo database
        """),
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update quotations in existing demo database instead of creating a new one",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        required=False,
        help="Start date for generating transactions (YYYY-MM-DD). Required for create mode.",
    )

    parser.add_argument(
        "--num-transactions",
        type=int,
        required=False,
        help="Number of transactions to generate. Required for create mode.",
    )

    parser.add_argument(
        "--initial-deposit",
        type=int,
        required=False,
        help="Initial deposit amount in EUR. Required for create mode.",
    )

    parser.add_argument(
        "--monthly-deposit",
        type=int,
        required=False,
        help="Monthly deposit in EUR. Required for create mode.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Validate arguments based on mode
    if args.update:
        # Update mode: check if demo DB exists
        if not os.path.exists(DATABASES["demo"]["NAME"]):
            logging.error("Cannot update: Demo database does not exist")
            logging.error(f"Expected location: {DATABASES['demo']['NAME']}")
            logging.error("Please create a demo database first without the --update flag")
            return

        logging.info("Running in UPDATE mode - updating quotations only")
        demo_db_path = Path(DATABASES["demo"]["NAME"]).resolve()
        logging.info(f"Using existing Demo DB: {demo_db_path}")

        # Ensure migrations are applied
        call_command("migrate", database="demo")

        # Update quotations
        generator = DBDemoGenerator()
        generator.update_quotations()
    else:
        # Create mode: validate required arguments
        if not all([args.start_date, args.num_transactions, args.initial_deposit, args.monthly_deposit]):
            logging.error(
                "Create mode requires: --start-date, --num-transactions, --initial-deposit, --monthly-deposit"
            )
            logging.error("Use --help for more information")
            return

        logging.info("Running in CREATE mode - generating new demo database")

        # Delete existing database if it exists
        if os.path.exists(DATABASES["demo"]["NAME"]):
            demo_db_path = Path(DATABASES["demo"]["NAME"]).resolve()
            logging.info(f"Deleting existing Demo DB: {demo_db_path}")
            os.remove(demo_db_path)

        # Generate new database
        generator = DBDemoGenerator()
        generator.generate(args.start_date, args.num_transactions, args.initial_deposit, args.monthly_deposit)

    # Close all database connections to ensure all data is written to disk
    logging.info("Closing database connections to flush data to disk...")
    connections.close_all()

    # Copy the generated/updated database to fixtures for distribution with Briefcase
    dev_demo_db = Path(DATABASES["demo"]["NAME"]).resolve()
    fixtures_demo_db = Path(__file__).parent.parent / "src" / "stonks_overwatch" / "fixtures" / "demo_db.sqlite3"

    logging.info("Copying demo DB to fixtures for distribution...")
    logging.info(f"  Source: {dev_demo_db}")
    logging.info(f"  Destination: {fixtures_demo_db}")

    # Ensure fixtures directory exists
    fixtures_demo_db.parent.mkdir(parents=True, exist_ok=True)

    # Copy the database
    shutil.copy2(dev_demo_db, fixtures_demo_db)

    logging.info("Demo DB successfully copied to fixtures directory")
    logging.info(f"Fixture size: {fixtures_demo_db.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()
