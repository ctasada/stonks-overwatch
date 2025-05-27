"""Imports all necessary data from DeGiro.

Django Database Dump/Load Script

This script provides functionality to:
1. Dump Django database content to a JSON file
2. Load database content from a JSON dump file

Usage:
    poetry run python ./scripts/dump_db.py --help
    poetry run python ./scripts/dump_db.py dump [--output filename.json]
    poetry run python ./scripts/dump_db.py load --input filename.json
"""

import argparse
import os
from pathlib import Path

# Django setup
import django
from django.apps import apps
from django.core import serializers
from django.core.management import call_command
from django.db import transaction

from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stonks_overwatch.settings')
    django.setup()

def get_models():
    """Get the necessary models for the database dump"""

    models = []
    for model in apps.get_models():
        app_label = model._meta.app_label

        if app_label in ['stonks_overwatch']:
            models.append(model)

    return models


def dump_database(output_file='db_dump.json'):
    """Dump database content to JSON file"""

    print(f"Dumping database to {output_file}...")

    # Get all objects from selected models
    objects_to_serialize = []
    for model in get_models():
        objects = model.objects.all()
        objects_to_serialize.extend(objects)
        print(f"Found {objects.count()} objects in {model._meta.app_label}.{model._meta.model_name}")

    # Serialize to JSON
    serialized_data = serializers.serialize('json', objects_to_serialize, indent=2)

    # Write to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(serialized_data)

    print(f"Successfully dumped {len(objects_to_serialize)} objects to {output_file}")


def load_database(input_file):
    """Load database content from the JSON file"""
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        return

    existing_db_file = Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath("db.sqlite3")

    if os.path.exists(existing_db_file):
        print(f"Warning: Existing database file '{existing_db_file}' found.")
        user_choice = (input("Would you like to exit (e), rename (r) or delete (d) the existing database file? " +
                             "(e/r/d): ").strip().lower())

        if user_choice == 'r':
            new_name = input("Enter the new name for the existing database file: ").strip()
            os.rename(existing_db_file, new_name)
            print(f"Database file renamed to '{new_name}'.")
        elif user_choice == 'd':
            os.remove(existing_db_file)
            print(f"Database file '{existing_db_file}' deleted.")
        elif user_choice == 'e':
            print("Exiting...")
            return
        else:
            print("Invalid choice. Aborting operation.")
            return

    print("Creating new database...")
    call_command("migrate")

    print(f"Loading database from {input_file}...")

    # Load data from a file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = f.read()

        # Deserialize and save
        objects_loaded = 0
        with transaction.atomic():
            for obj in serializers.deserialize('json', data):
                obj.save()
                objects_loaded += 1

        print(f"Successfully loaded {objects_loaded} objects from {input_file}")

    except Exception as e:
        print(f"Error loading data: {e}")
        return


def main():
    parser = argparse.ArgumentParser(description='Django Database Dump/Load Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump database to file')
    dump_parser.add_argument('--output', '-o', default='db_dump.json',
                             help='Output file name (default: db_dump.json)')

    # Load command
    load_parser = subparsers.add_parser('load', help='Load database from file')
    load_parser.add_argument('--input', '-i', required=True,
                             help='Input file name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup Django
    setup_django()

    if args.command == 'dump':
        dump_database(output_file=args.output)
    elif args.command == 'load':
        load_database(input_file=args.input)


if __name__ == '__main__':
    main()
