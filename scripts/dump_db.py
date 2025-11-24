"""Imports all necessary data from DeGiro.

Django Database Dump/Load Script

This script provides functionality to:
1. Dump Django database content to a JSON file
2. Load database content from a JSON dump file

Usage:
    poetry run python -m scripts.dump_db --help
    poetry run python -m scripts.dump_db dump [--output filename.json]
    poetry run python -m scripts.dump_db.py load --input filename.json
"""

import argparse
import os

# Django setup
from django.core import serializers
from django.core.management import call_command
from django.db import transaction

from scripts.common import setup_script_environment

# Set up Django environment and logging
setup_script_environment()

from stonks_overwatch.settings import DATABASES  # noqa: E402
from stonks_overwatch.utils.database.db_utils import dump_database  # noqa: E402


def load_database(input_file, database="default"):
    """Load database content from the JSON file"""
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        return

    if database == "demo":
        os.environ["DEMO_MODE"] = "True"

    existing_db_file = DATABASES[database]["NAME"]

    if os.path.exists(existing_db_file):
        print(f"Warning: Existing database file '{existing_db_file}' found.")
        user_choice = (
            input("Would you like to exit (x), rename (r) or delete (d) the existing database file? " + "(x/r/d): ")
            .strip()
            .lower()
        )

        if user_choice == "r":
            new_name = input("Enter the new name for the existing database file: ").strip()
            os.rename(existing_db_file, new_name)
            print(f"Database file renamed to '{new_name}'.")
        elif user_choice == "d":
            os.remove(existing_db_file)
            print(f"Database file '{existing_db_file}' deleted.")
        elif user_choice == "x":
            print("Exiting...")
            return
        else:
            print("Invalid choice. Aborting operation.")
            return

    print("Creating new database...")
    call_command("migrate", database=database)

    print(f"Loading database from {input_file}...")

    # Load data from a file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = f.read()

        # Deserialize and save to the correct database
        objects_loaded = 0
        with transaction.atomic(using=database):
            for obj in serializers.deserialize("json", data):
                obj.save(using=database)
                objects_loaded += 1

        print(f"Successfully loaded {objects_loaded} objects from {input_file}")

    except Exception as e:
        print(f"Error loading data: {e}")
        return


def main():
    parser = argparse.ArgumentParser(description="Django Database Dump/Load Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Dump command
    dump_parser = subparsers.add_parser("dump", help="Dump database to file")
    dump_parser.add_argument("--output", "-o", default="db_dump.zip", help="Output file name (default: db_dump.zip)")
    dump_parser.add_argument(
        "--database",
        "-d",
        default="default",
        choices=["default", "demo"],
        help="Database to use (default: default, options: default, demo)",
    )

    # Load command
    load_parser = subparsers.add_parser("load", help="Load database from file")
    load_parser.add_argument("--input", "-i", required=True, help="Input file name")
    load_parser.add_argument(
        "--database",
        "-d",
        default="default",
        choices=["default", "demo"],
        help="Database to use (default: default, options: default, demo)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "dump":
        dump_database(output_file=args.output, database=args.database)
    elif args.command == "load":
        load_database(input_file=args.input, database=args.database)


if __name__ == "__main__":
    main()
