"""
poetry run python ./scripts/check_updates.py
"""

import argparse
import logging

from common import init_logger

from stonks_overwatch.services.utilities.google_drive_service import GoogleDriveService


def handle_list_command(args):
    files_info = GoogleDriveService.list_files(args.folder_id)
    if args.latest:
        latest_files = GoogleDriveService.get_latest_by_platform(files_info)
        logging.info("Latest versions by platform:")
        for _ext, f in latest_files.items():
            logging.info(f"{f.name}\t{f.id}\t{f.version}\t{f.extension}")
    else:
        for f in files_info:
            logging.info(f"{f.name}\t{f.id}\t{f.version}\t{f.extension}")


def handle_download_command(args):
    success = GoogleDriveService.download_file(args.file_id, args.output)
    if not success:
        exit(1)


def handle_latest_command(args):
    files_info = GoogleDriveService.list_files(args.folder_id)
    latest_files = GoogleDriveService.get_latest_by_platform(files_info)
    if args.platform:
        if args.platform in latest_files:
            f = latest_files[args.platform]
            output_path = f"{args.output_dir}/{f.name}"
            logging.info(f"Downloading latest {args.platform}: {f.name}")
            success = GoogleDriveService.download_file(f.id, output_path)
            if not success:
                exit(1)
        else:
            logging.info(f"No files found for platform: {args.platform}")
            exit(1)
    else:
        for _ext, f in latest_files.items():
            output_path = f"{args.output_dir}/{f.name}"
            logging.info(f"Downloading {f.name}...")
            success = GoogleDriveService.download_file(f.id, output_path)
            if not success:
                logging.info(f"Failed to download {f.name}")
                exit(1)


def main() -> None:
    init_logger()
    parser = argparse.ArgumentParser(description="Google Drive public folder utility")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List files in a folder")
    list_parser.add_argument(
        "folder_id",
        nargs="?",
        default=GoogleDriveService.DEFAULT_FOLDER_ID,
        help="Google Drive folder ID (default: %(default)s)",
    )
    list_parser.add_argument("--latest", action="store_true", help="Show only the latest version for each platform")

    download_parser = subparsers.add_parser("download", help="Download a file by ID")
    download_parser.add_argument("file_id", help="Google Drive file ID")
    download_parser.add_argument("output", help="Output file path")

    latest_parser = subparsers.add_parser("latest", help="Download the latest version")
    latest_parser.add_argument(
        "folder_id", nargs="?", default=GoogleDriveService.DEFAULT_FOLDER_ID, help="Google Drive folder ID"
    )
    latest_parser.add_argument("--platform", choices=["dmg", "msi", "flatpak"], help="Specific platform to download")
    latest_parser.add_argument("--output-dir", default=".", help="Output directory (default: current directory)")

    args = parser.parse_args()

    if args.command == "list":
        handle_list_command(args)
    elif args.command == "download":
        handle_download_command(args)
    elif args.command == "latest":
        handle_latest_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
