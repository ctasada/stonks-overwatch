"""
poetry run python -m scripts.check_updates

For private repositories, set the GITHUB_TOKEN environment variable:
    export GITHUB_TOKEN=your_github_personal_access_token
    poetry run python -m scripts.check_updates list

To create a token:
    1. Go to GitHub Settings > Developer settings > Personal access tokens
    2. Generate new token with 'repo' scope (for private repos) or 'public_repo' (for public repos)
    3. Copy the token and set it as GITHUB_TOKEN environment variable
"""

import argparse
import logging
import os

from scripts.common import setup_script_environment

# Set up Django environment and logging
setup_script_environment()

# Import application modules after setup
from stonks_overwatch.services.utilities.github_release_service import GitHubReleaseService  # noqa: E402


def check_github_token():
    """Check if GitHub token is set and provide helpful message if not."""
    if not os.environ.get("GITHUB_TOKEN"):
        logging.warning(
            "GITHUB_TOKEN not set. If the repository is private, you may encounter authentication errors.\n"
            "Set the GITHUB_TOKEN environment variable:\n"
            "  export GITHUB_TOKEN=your_github_personal_access_token\n"
        )


def handle_list_command(args):
    release_assets = GitHubReleaseService.list_releases(args.owner, args.repo, args.include_prereleases)
    if args.latest:
        latest_assets = GitHubReleaseService.get_latest_by_platform(release_assets)
        logging.info("Latest versions by platform:")
        for _ext, asset in latest_assets.items():
            logging.info(
                f"{asset.name}\t{asset.version}\t{asset.extension}\t{asset.release_tag}\n"
                f"  Download URL: {asset.download_url}"
            )
    else:
        for asset in release_assets:
            logging.info(
                f"{asset.name}\t{asset.version}\t{asset.extension}\t{asset.release_tag}\n"
                f"  Download URL: {asset.download_url}"
            )


def handle_download_command(args):
    release_assets = GitHubReleaseService.list_releases(args.owner, args.repo)
    # Find the asset by name
    asset = next((a for a in release_assets if a.name == args.asset_name), None)
    if not asset:
        logging.error(f"Asset '{args.asset_name}' not found")
        exit(1)

    success = GitHubReleaseService.download_asset(asset.download_url, args.output, api_url=asset.api_url)
    if not success:
        exit(1)


def handle_latest_command(args):
    release_assets = GitHubReleaseService.list_releases(args.owner, args.repo)
    latest_assets = GitHubReleaseService.get_latest_by_platform(release_assets)
    if args.platform:
        if args.platform in latest_assets:
            asset = latest_assets[args.platform]
            output_path = f"{args.output_dir}/{asset.name}"
            logging.info(f"Downloading latest {args.platform}: {asset.name}")
            logging.info(f"Download URL: {asset.download_url}")
            logging.info(f"Output path: {output_path}")
            success = GitHubReleaseService.download_asset(asset.download_url, output_path, api_url=asset.api_url)
            if not success:
                logging.error(f"Failed to download {asset.name}")
                exit(1)
        else:
            logging.info(f"No files found for platform: {args.platform}")
            exit(1)
    else:
        for _ext, asset in latest_assets.items():
            output_path = f"{args.output_dir}/{asset.name}"
            logging.info(f"Downloading {asset.name}...")
            logging.info(f"Download URL: {asset.download_url}")
            success = GitHubReleaseService.download_asset(asset.download_url, output_path, api_url=asset.api_url)
            if not success:
                logging.error(f"Failed to download {asset.name}")
                exit(1)


def main() -> None:
    check_github_token()

    parser = argparse.ArgumentParser(
        description="GitHub Releases utility for Stonks Overwatch",
        epilog="For private repositories, set GITHUB_TOKEN environment variable",
    )
    parser.add_argument(
        "--owner",
        default=GitHubReleaseService.DEFAULT_REPO_OWNER,
        help=f"GitHub repository owner (default: {GitHubReleaseService.DEFAULT_REPO_OWNER})",
    )
    parser.add_argument(
        "--repo",
        default=GitHubReleaseService.DEFAULT_REPO_NAME,
        help=f"GitHub repository name (default: {GitHubReleaseService.DEFAULT_REPO_NAME})",
    )

    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List release assets")
    list_parser.add_argument("--latest", action="store_true", help="Show only the latest version for each platform")
    list_parser.add_argument(
        "--include-prereleases", action="store_true", help="Include pre-release versions in the list"
    )

    download_parser = subparsers.add_parser("download", help="Download a specific asset by name")
    download_parser.add_argument("asset_name", help="Name of the asset to download")
    download_parser.add_argument("output", help="Output file path")

    latest_parser = subparsers.add_parser("latest", help="Download the latest version")
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
