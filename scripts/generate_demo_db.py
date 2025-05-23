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
from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR, STONKS_OVERWATCH_DB_NAME  # noqa: E402

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
        # FIXME: Should randomly sell products. Only if already bought.
        buysell = "B" # Buy or Sell (B or S)

        trading_venue : str = ""
        for exchange in self.products_config["exchanges"]:
            if exchange["id"] == product.exchange_id:
                trading_venue = exchange["tradingVenue"]
                break

        # Calculate values
        quotations = ProductQuotationsRepository.get_product_quotations(product_id)
        logging.info(f"Creating entry for date: {date}")
        logging.info(f"{date} = {date.strftime(LocalizationUtility.DATE_FORMAT)}")
        logging.info(f"Quotations for {product_id} ({LIST_OF_PRODUCTS[product_id]['symbol']}): {quotations}")
        value = quotations[date.strftime(LocalizationUtility.DATE_FORMAT)]
        max_quantity = int(abs(balance) // abs(value))
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
        change_in_base_currency = change
        if currency != "EUR":
            exchange_rate = self.currency_converter.convert(
                amount=1.0,
                currency=currency,
                new_currency="EUR",
                fx_date=date.date()
            )
            auto_fx_fee = -1.00 * exchange_rate
            change_in_base_currency = change / exchange_rate

        transaction_date = self.update_random_time(date)

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

        # Transactions
        # Example: 2025-03-20 11:04:48 Buy VUSA 4 @ 99.00 EUR = -396.00 EUR + 1.00 EUR Fee
        # Example: 2024-11-21 20:05:31 Buy KO 10 @ $ 63.63 = -636.30 USD (€ -606.87) + 2.00 EUR Fee

        description = "DEGIRO Transactiekosten en/of kosten van derden"
        transaction_type = "CASH_TRANSACTION"

        #description = "Degiro Cash Sweep Transfer"
        #transaction_type = "FLATEX_CASH_SWEEP"

        movement_date = transaction_date.strftime(LocalizationUtility.TIME_DATE_FORMAT)
        movement_value_date = self.update_random_time(transaction_date)

        # Calculate balances
        balance_unsettled_cash = balance + change
        balance_flatex = balance
        balance_cash_fund = []
        balance_total = balance_unsettled_cash
        # change_in_base_currency + fees

        logging.info(f"Original balance: {balance}")
        logging.info(f"Change: {change}")
        logging.info(f"Balance Total: {balance_total}")
        logging.info(f"Balance Unsettled: {balance_unsettled_cash}")
        logging.info(f"Balance Flatex: {balance_flatex}")

        order_id = f"ORD{random.randint(10000, 99999)}"

        if currency == "EUR":
            exchange_rate = None

        DeGiroCashMovements.objects.create(
            date=movement_date,
            value_date=movement_value_date,
            description=description,
            currency=currency,
            type=transaction_type,
            balance_unsettled_cash=str(balance_unsettled_cash),
            balance_flatex_cash=str(balance_flatex),
            balance_cash_fund=str(balance_cash_fund),
            balance_total=str(balance_total),
            product_id=product_id,
            change=change,
            exchange_rate=exchange_rate,
            order_id=order_id
        )

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

        if currency != "EUR":
            DeGiroCashMovements.objects.create(
                date=movement_date,
                value_date=movement_value_date,
                description=description,
                currency=currency,
                type="FLATEX_CASH_SWEEP",
                balance_unsettled_cash=str(balance_unsettled_cash),
                balance_flatex_cash=str(balance_flatex),
                balance_cash_fund=str(balance_cash_fund),
                balance_total=str(balance_total),
                product_id=product_id,
                change=change,
                exchange_rate=exchange_rate,
                order_id=order_id
            )

        # Cash Movements
        # Example: 2025-03-20 11:04:48 Buy VUSA 4 @ 99.00 EUR = -396.00 EUR + 1.00 EUR Fee
        # {
        #     "id": "2346742449",
        #     "date": "2025-03-20 11:04:48",
        #     "value_date": "2025-03-20 11:04:48",
        #     "description": "DEGIRO Transactiekosten en/of kosten van derden",
        #     "currency": "EUR",
        #     "type": "CASH_TRANSACTION",
        #     "balance_unsettled_cash": "-397.0",
        #     "balance_flatex_cash": "429.74",
        #     "balance_cash_fund": "[{'participation': 0.0, 'id': 15694501, 'price': 10573.79}, {'participation': 0.0, 'id': 15694498, 'price': 10573.79}]",
        #     "balance_total": "32.74",
        #     "product_id": "4587473",
        #     "change": "-1",
        #     "exchange_rate": "",
        #     "order_id": "bebaa8b6-5884-4a79-83bb-bb9a684c20c0"
        # },
        # {
        #     "id": "2346810286",
        #     "date": "2025-03-20 12:41:05",
        #     "value_date": "2025-03-20 12:41:05",
        #     "description": "Degiro Cash Sweep Transfer",
        #     "currency": "EUR",
        #     "type": "FLATEX_CASH_SWEEP",
        #     "balance_unsettled_cash": "0.0",
        #     "balance_flatex_cash": "429.74",
        #     "balance_cash_fund": "[{'participation': 0.0, 'id': 15694501, 'price': 10573.79}, {'participation': 0.0, 'id': 15694498, 'price': 10573.79}]",
        #     "balance_total": "429.74",
        #     "product_id": "",
        #     "change": "397",
        #     "exchange_rate": "",
        #     "order_id": ""
        # },
        # {
        #     "id": "2346810287",
        #     "date": "2025-03-20 12:41:05",
        #     "value_date": "2025-03-20 12:41:05",
        #                    "Transfer from your cash account at flatexDEGIRO Bank 397 EUR"
        #     "description": "Overboeking van uw geldrekening bij flatexDEGIRO Bank 397 EUR",
        #     "currency": "EUR",
        #     "type": "FLATEX_CASH_SWEEP",
        #     "balance_unsettled_cash": "0.0",
        #     "balance_flatex_cash": "32.74",
        #     "balance_cash_fund": "[{'participation': 0.0, 'id': 15694501, 'price': 10573.79}, {'participation': 0.0, 'id': 15694498, 'price': 10573.79}]",
        #     "balance_total": "32.74",
        #     "product_id": "",
        #     "change": "",
        #     "exchange_rate": "",
        #     "order_id": ""
        # }

        # Cash Movements
        # Example: 2024-11-21 20:05:31 Buy KO 10 @ $ 63.63 = -636.30 USD (€ -606.87) + 2.00 EUR Fee
        # {
        #     "id": "2209865277",
        #     "date": "2024-11-21 20:05:31",
        #     "value_date": "2024-11-21 20:05:31",
        #     "description": "DEGIRO Transactiekosten en/of kosten van derden",
        #     "currency": "EUR",
        #     "type": "CASH_TRANSACTION",
        #     "balance_unsettled_cash": "-2.0",
        #     "balance_flatex_cash": "702.92",
        #     "balance_cash_fund": "[{'participation': 0.0, 'id': 15694501, 'price': 10477.07}, {'participation': 0.0, 'id': 15694498, 'price': 10477.07}]",
        #     "balance_total": "700.92",
        #     "product_id": "331829",
        #     "change": "-2",
        #     "exchange_rate": "",
        #     "order_id": "9392df05-8f1c-48aa-8f8a-da175329346e"
        # },
        # {
        #     "id": "2209865279",
        #     "date": "2024-11-21 20:05:31",
        #     "value_date": "2024-11-21 20:05:31",
        #     "description": "Valuta Debitering",
        #     "currency": "EUR",
        #     "type": "CASH_TRANSACTION",
        #     "balance_unsettled_cash": "-610.39",
        #     "balance_flatex_cash": "702.92",
        #     "balance_cash_fund": "[{'participation': 0.0, 'id': 15694501, 'price': 10477.07}, {'participation': 0.0, 'id': 15694498, 'price': 10477.07}]",
        #     "balance_total": "92.53",
        #     "product_id": "331829",
        #     "change": "-608.39",
        #     "exchange_rate": "",
        #     "order_id": "9392df05-8f1c-48aa-8f8a-da175329346e"
        # },
        # {
        #     "id": "2209865280",
        #     "date": "2024-11-21 20:05:31",
        #     "value_date": "2024-11-21 20:05:31",
        #     "description": "Valuta Creditering",
        #     "currency": "USD",
        #     "type": "CASH_TRANSACTION",
        #     "balance_unsettled_cash": "0.0",
        #     "balance_flatex_cash": "nan",
        #     "balance_cash_fund": "nan",
        #     "balance_total": "0.0",
        #     "product_id": "331829",
        #     "change": "636.3",
        #     "exchange_rate": "1459",
        #     "order_id": "9392df05-8f8a-da175329346e"
        # }

        # FIXME: This value should be always in EUR
        return balance + change


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
            # If Saturday (5), add 2 days; if Sunday (6), add 1 day
            if transaction_date.weekday() == 5:
                transaction_date += timedelta(days=2)
            elif transaction_date.weekday() == 6:
                transaction_date += timedelta(days=1)

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

    if os.path.exists(Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME)):
        demo_db_path = Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME)
        logging.info(f"Deleting existing Demo DB: {demo_db_path}")
        os.remove(Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath(STONKS_OVERWATCH_DB_NAME))

    """Main function to run the script."""
    generator = DBDemoGenerator()
    generator.generate(args.start_date, args.num_transactions, args.initial_deposit)

if __name__ == "__main__":
    main()
