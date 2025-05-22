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
from decimal import Decimal

import django
from degiro_connector.quotecast.models.chart import Interval
from django.core.management import call_command

from stonks_overwatch.services.degiro.constants import TransactionType
from stonks_overwatch.utils.datetime import DateTimeUtility
from stonks_overwatch.utils.localization import LocalizationUtility

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stonks_overwatch.settings')
django.setup()

# The import is defined here, so all the Django configuration can be executed
from stonks_overwatch.repositories.degiro.models import (  # noqa: E402
    DeGiroCashMovements,
    DeGiroCompanyProfile,
    DeGiroProductInfo,
    DeGiroProductQuotation,
    DeGiroTransactions,
)
from stonks_overwatch.services.degiro.degiro_service import DeGiroService  # noqa: E402

LIST_OF_PRODUCTS = {
    "5462588": {
        "id": "5462588",
        "name": "Advanced Micro Devices Inc",
        "isin": "US0079031078",
        "symbol": "AMD",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "332111": {
        "id": "332111",
        "name": "Microsoft Corp",
        "isin": "US5949181045",
        "symbol": "MSFT",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "4587473": {
        "id": "4587473",
        "name": "Vanguard S&P 500 UCITS ETF USD",
        "isin": "IE00B3XXRP09",
        "symbol": "VUSA",
        "productType": "ETF",
        "currency": "EUR",
        "quotations": []
    },
    "1147582": {
        "id": "1147582",
        "name": "NVIDIA Corp",
        "isin": "US67066G1040",
        "symbol": "NVDA",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "331829": {
        "id": "331829",
        "name": "Coca-Cola",
        "isin": "US1912161007",
        "symbol": "KO",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "18333971": {
        "id": "18333971",
        "name": "Palantir Technologies Inc",
        "isin": "US69608A1088",
        "symbol": "PLTR",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "331824": {
        "id": "331824",
        "name": "JPMorgan Chase & Co",
        "isin": "US46625H1005",
        "symbol": "JPM",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "331868": {
        "id": "331868",
        "name": "Apple Inc",
        "isin": "US0378331005",
        "symbol": "AAPL",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "322171": {
        "id": "322171",
        "name": "Intel Corp",
        "isin": "US4581401001",
        "symbol": "INTC",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "331941": {
        "id": "331941",
        "name": "Johnson & Johnson",
        "isin": "US4781601046",
        "symbol": "JNJ",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    },
    "331986": {
        "id": "331986",
        "name": "Walt Disney",
        "isin": "US2546871060",
        "symbol": "DIS",
        "productType": "STOCK",
        "currency": "USD",
        "quotations": []
    }
}

class DBDemoGenerator:
    """Class to generate a demo DB with random data."""

    def __init__(self):
        self.degiro_service = DeGiroService()

    @staticmethod
    def update_random_time(date: datetime) -> datetime:
        random_hour = random.randint(9, 22)
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
        product_ids = list(LIST_OF_PRODUCTS.keys())

        # Generate random values
        product_id = random.choice(product_ids)
        transaction_type = "TRANSACTION"
        currency = LIST_OF_PRODUCTS[product_id]["currency"]
        value = 52.39 # Value from Quotations
        quantity = 20 # Random quantity
        description = f"Koop {quantity} @ {value} {currency}"

        # Generate random amounts
        change = value * quantity
        # FIXME: Should read the FX for that day and do the calculation. Only if currency is not EUR
        exchange_rate = Decimal(str(random.uniform(0.8, 1.2))).quantize(Decimal('0.0001'))

        # Calculate balances
        balance_flatex = Decimal(str(random.uniform(0, 5000))).quantize(Decimal('0.01'))
        balance_cash_fund = Decimal(str(random.uniform(0, 5000))).quantize(Decimal('0.01'))
        balance_unsettled = balance - change
        balance_total = balance_unsettled

        transaction_date = self.update_random_time(date)

        cash_movement = DeGiroCashMovements.objects.create(
            date=transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            value_date=(transaction_date + timedelta(days=random.randint(0, 2)))
                            .strftime(LocalizationUtility.TIME_DATE_FORMAT),
            description=description,
            currency=currency,
            type=transaction_type,
            balance_unsettled_cash=str(balance_unsettled),
            balance_flatex_cash=str(balance_flatex),
            balance_cash_fund=str(balance_cash_fund),
            balance_total=str(balance_total),
            product_id=product_id,
            change=change,
            exchange_rate=exchange_rate,
            order_id=f"ORD{random.randint(10000, 99999)}"
        )

        DeGiroTransactions.objects.create(
            id=str(cash_movement.id),
            product_id=product_id,
            date=transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT),
            buysell="BUY",
            price=value,
            quantity=quantity,
            total=change,
            order_type_id=0, # FIXME: I don't know what this is
            counter_party="MK",
            transfered="0",
            fx_rate=exchange_rate,
            nett_fx_rate=exchange_rate,
            gross_fx_rate=exchange_rate,
            auto_fx_fee_in_base_currency="0",
            total_in_base_currency=change, # FIXME: Should be the amount in EUR and negative (since it's a buy)
            fee_in_base_currency="0",
            total_fees_in_base_currency="0",
            total_plus_fee_in_base_currency=change, # FIXME: Should be the amount in EUR and negative (since it's a buy)
            # FIXME: Should be the amount in EUR and negative (since it's a buy)
            total_plus_all_fees_in_base_currency=change,
            transaction_type_id=TransactionType.BUY_SELL.value,
            trading_venue="XETRA",
            executing_entity_id="4PQUHN3JPFGFNF3BB653"
        )

        return balance - change #FIXME: Should be the amount in EUR and negative (since it's a buy)


    def create_deposit(self, date: datetime, amount: float) -> None:
        """Create the initial deposit transaction.

        Args:
            date: The date for the initial deposit
            amount: The amount of the initial deposit

        Returns:
            DeGiroCashMovements: The initial deposit transaction
        """
        deposit_datetime = self.update_random_time(date)

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

        products_info = self.degiro_service.get_products_info(list(LIST_OF_PRODUCTS.keys()))
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

            # Get the company profile
            company_profile = self.degiro_service.get_client().get_company_profile(
                product_isin=row["isin"],
                raw=True,
            )
            DeGiroCompanyProfile.objects.update_or_create(isin=key, defaults={"data": company_profile})

    def generate(self, from_date: str, num_transactions: int, initial_deposit: float) -> None:
        # Parse start date
        start_date = datetime.strptime(from_date, LocalizationUtility.DATE_FORMAT)
        end_date = datetime.now()

        # Calculate time delta between start and end date
        total_days = (end_date - start_date).days

        logging.info("Creating demo DB with random data ...")
        call_command("migrate")

        # Create ProductsInfo
        logging.info("Creating products info ...")
        self.create_products_info(from_date)

        # Generate transactions
        balance: float = initial_deposit
        # Add initial deposit as first transaction
        self.create_deposit(start_date, balance)

        # Generate remaining transactions
        for i in range(num_transactions):
            # Calculate a date between start_date and end_date
            days_to_add = (total_days * i) // (num_transactions - 1)
            transaction_date = start_date + timedelta(days=days_to_add)

            # Generate a random cash movement
            balance = self.generate_random_transaction(transaction_date, balance)

        # Save all transactions
        logging.info(f"Created {num_transactions} cash movements")


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

    return parser.parse_args()

def main():
    init()
    args = parse_args()

    """Main function to run the script."""
    generator = DBDemoGenerator()
    generator.generate(args.start_date, args.num_transactions, args.initial_deposit)

if __name__ == "__main__":
    main()
