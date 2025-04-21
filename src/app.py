#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent
DEFAULT_SERVER_PORT = 8000
DEFAULT_SERVER_HOST = '0.0.0.0'

DJANGO_MANAGE_PATH = os.path.join(BASE_PATH, 'src', 'manage.py')

def run_command(command):
    """Run a command and print its output."""
    try:
        result = subprocess.run(command, check=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def npm_install():
    print("Installing NodeJs dependencies...")
    run_command(['python', DJANGO_MANAGE_PATH, 'npminstall'])

def run_migrations():
    print("Running migrations...")
    run_command(['python', DJANGO_MANAGE_PATH, 'makemigrations'])
    run_command(['python', DJANGO_MANAGE_PATH, 'migrate'])

def start_server(host, port):
    print(f"Starting development server on {host}:{port}...")
    run_command([
        'python',
        DJANGO_MANAGE_PATH,
        'runserver',
        f'{host}:{port}',
        '--noreload',  # Disable autoreload to avoid issues with subprocesses
    ])

def main():
    parser = argparse.ArgumentParser(description='Run Django management commands')
    parser.add_argument('--debug', action='store_true',  help='Enables debug mode')
    parser.add_argument('--profile', action='store_true',  help='Enables profiling mode')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # npminstall command
    subparsers.add_parser('npminstall', help='Install NodeJs dependencies')

    # Migrate command
    subparsers.add_parser('migrate', help='Run database migrations')

    # Runserver command
    runserver_parser = subparsers.add_parser('runserver', help='Start development server')
    runserver_parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_SERVER_PORT,
        help=f"Port to run the server on (default: {DEFAULT_SERVER_PORT})"
    )
    runserver_parser.add_argument(
        '--host',
        type=str,
        default=DEFAULT_SERVER_HOST,
        help=f"Host to run the server on (default: {DEFAULT_SERVER_HOST})"
    )

    args = parser.parse_args()

    # Set debug and profile modes based on command line arguments
    if args.debug:
        os.environ['DEBUG_MODE'] = 'True'
    if args.profile:
        os.environ['PROFILE_MODE'] = 'True'

    # If no command is provided, run both migrate and runserver
    if not args.command:
        npm_install()
        run_migrations()
        start_server(DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT)
        return

    if args.command == 'npminstall':
        npm_install()
    elif args.command == 'migrate':
        run_migrations()
    elif args.command == 'runserver':
        start_server(args.host, args.port)

if __name__ == '__main__':
    main()
