import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List

from scripts.common import setup_django_environment

# Set up environment BEFORE importing stonks_overwatch modules
# This adds 'src' to sys.path
setup_django_environment()

from stonks_overwatch.core.registry_setup import ensure_registry_initialized  # noqa: E402
from stonks_overwatch.services.brokers.metatrader4.utilities.parser import parse_mt4_html  # noqa: E402

ensure_registry_initialized()

from stonks_overwatch.config.metatrader4 import MetaTrader4Config  # noqa: E402
from stonks_overwatch.services.brokers.metatrader4.client.metatrader4_client import MetaTrader4Client  # noqa: E402

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def calculate_calendar(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate buy transactions by date and item."""
    # Date -> Item -> Stats
    # Using nested setdefault instead of lambda to allow pickling if necessary,
    # though here nested dicts are fine.
    # stats structure: { date: { item: { 'TP': 0, 'Profit': 0.0 } } }
    stats = defaultdict(lambda: defaultdict(lambda: {"TP": 0, "Profit": 0.0}))

    for t in transactions:
        if t.get("Type") == "buy":
            # "Close Time" format expected: "YYYY.MM.DD HH:MM:SS"
            close_time = t.get("Close Time", "")
            if not close_time:
                continue

            date = close_time.split(" ")[0]
            if not date:
                continue

            item = t.get("Item", "Unknown")
            profit_str = t.get("Profit", "0").replace(" ", "")
            try:
                profit = float(profit_str)
            except ValueError:
                profit = 0.0

            stats[date][item]["TP"] += 1
            stats[date][item]["Profit"] += profit

    # Convert to sorted dicts for clean JSON output
    sorted_dates = sorted(stats.keys())
    result = {}
    for date in sorted_dates:
        result[date] = dict(stats[date])
        # Sort items and round profits
        for item in result[date]:
            result[date][item]["Profit"] = round(result[date][item]["Profit"], 2)

    return result


def process_output(args, data_dict: Dict[str, Any]):
    """Handle the output of parsed data."""
    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump(data_dict, f, indent=2)
            logger.info(f"Data saved to {args.output}")
        except IOError as e:
            logger.error(f"Failed to write output file: {e}")
            sys.exit(1)

    # If verbose or no output file specified, print to stdout
    if args.verbose or not args.output:
        print(json.dumps(data_dict, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Parse MetaTrader 4 HTML Statement")
    parser.add_argument("input", nargs="?", help="Path to the .htm statement file")
    parser.add_argument("-o", "--output", help="Output JSON file path", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Print parsed data to stdout")
    parser.add_argument("--show_calendar", action="store_true", help="Show calendar aggregation of 'buy' transactions")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    content = None

    if not args.input:
        logger.info("No input file provided. Attempting to retrieve from FTP...")
        try:
            # Load configuration
            config = MetaTrader4Config.default()
            client = MetaTrader4Client(config)
            content = client.get_report_content()
        except Exception as e:
            logger.error(f"Failed to retrieve from FTP: {e}")
            sys.exit(1)

    elif not os.path.exists(args.input):
        logger.error(f"File not found: {args.input}")
        sys.exit(1)
    else:
        try:
            with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            sys.exit(1)

    if not content:
        logger.error("No content available to parse.")
        sys.exit(1)

    try:
        parsed_data = parse_mt4_html(content)

        if args.show_calendar:
            calendar_data = calculate_calendar(parsed_data.closed_transactions)
            print(json.dumps(calendar_data, indent=2))
            sys.exit(0)

        data_dict = parsed_data.to_dict()
        process_output(args, data_dict)

    except Exception:
        logger.exception("An unexpected error occurred during parsing")
        sys.exit(1)


if __name__ == "__main__":
    main()
