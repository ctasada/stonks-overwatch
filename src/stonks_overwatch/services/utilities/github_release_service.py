import os
import platform as py_platform
import re
from typing import List, Optional

import requests
from packaging.version import InvalidVersion, Version

from stonks_overwatch.utils.core.logger import StonksLogger


class GitHubReleaseService:
    logger = StonksLogger.get_logger("stonks_overwatch.github_release_service", "[GITHUB_RELEASE|SERVICE]")

    # Default repository information
    DEFAULT_REPO_OWNER = "ctasada"
    DEFAULT_REPO_NAME = "stonks-overwatch"

    @staticmethod
    def _get_headers() -> dict:
        """
        Get headers for GitHub API requests, including authentication if available.

        Returns:
            Dictionary of headers including Authorization if GITHUB_TOKEN is set
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Stonks-Overwatch",
        }

        # Check for GitHub token in environment
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            GitHubReleaseService.logger.debug("Using GitHub authentication token")

        return headers

    class AssetInfo:
        def __init__(self, name: str, download_url: str, size: int, release_tag: str, api_url: str = None) -> None:
            self.name: str = name
            self.download_url: str = download_url
            self.api_url: str = api_url or download_url  # API URL for authenticated downloads
            self.size: int = size
            self.release_tag: str = release_tag
            self.version: Optional[Version] = self.extract_version()
            self.extension: Optional[str] = self.extract_extension()

        def extract_version(self) -> Optional[Version]:
            # First try to extract from the release tag (e.g., v0.1.0 or 0.1.0)
            tag_match = re.search(r"v?([0-9]+\.[0-9]+\.[0-9]+)", self.release_tag)
            if tag_match:
                try:
                    return Version(tag_match.group(1))
                except InvalidVersion:
                    pass

            # Fallback: extract from filename (support Stonks.Overwatch-0.1.0, Stonks_Overwatch-0.1.0-x86_64, etc.)
            name_match = re.search(r"Stonks[._]Overwatch-([0-9]+\.[0-9]+\.[0-9]+)(?:-[\w]+)?", self.name)
            if name_match:
                try:
                    return Version(name_match.group(1))
                except InvalidVersion:
                    pass

            return None

        def extract_extension(self) -> Optional[str]:
            # Extract extension at the end, e.g. .dmg, .msi, .flatpak, possibly after -macos, -x86_64, etc.
            match = re.search(r"(?:-[\w]+)?\.(dmg|msi|flatpak)$", self.name)
            if match:
                return match.group(1)
            return None

        def __repr__(self) -> str:
            return f"AssetInfo(name={self.name}, version={self.version}, ext={self.extension}, tag={self.release_tag})"

    @staticmethod
    def list_releases(
        repo_owner: str = DEFAULT_REPO_OWNER,
        repo_name: str = DEFAULT_REPO_NAME,
        include_prereleases: bool = False,
    ) -> List["GitHubReleaseService.AssetInfo"]:
        """
        List all release assets from the GitHub repository.

        Args:
            repo_owner: GitHub repository owner/organization
            repo_name: GitHub repository name
            include_prereleases: Whether to include pre-release versions

        Returns:
            List of AssetInfo objects for all assets in all releases
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        headers = GitHubReleaseService._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                GitHubReleaseService.logger.error(
                    f"Repository not found: {repo_owner}/{repo_name}. "
                    "Please check:\n"
                    "  1. Repository exists and name is correct\n"
                    "  2. Repository is public OR set GITHUB_TOKEN environment variable for private repos\n"
                    "  3. Repository has at least one release published"
                )
                return []

            if response.status_code == 401:
                GitHubReleaseService.logger.error(
                    "GitHub API authentication failed. Please check your GITHUB_TOKEN environment variable is valid."
                )
                return []

            response.raise_for_status()
            releases = response.json()

            if not releases:
                GitHubReleaseService.logger.warning(
                    f"No releases found for {repo_owner}/{repo_name}. "
                    "Create a release on GitHub to enable update checking."
                )
                return []

            assets = []
            for release in releases:
                # Skip pre-releases if requested
                if not include_prereleases and release.get("prerelease", False):
                    GitHubReleaseService.logger.debug(f"Skipping pre-release: {release.get('tag_name', 'unknown')}")
                    continue

                # Skip drafts
                if release.get("draft", False):
                    GitHubReleaseService.logger.debug(f"Skipping draft: {release.get('tag_name', 'unknown')}")
                    continue

                tag_name = release.get("tag_name", "")
                for asset in release.get("assets", []):
                    asset_name = asset.get("name", "")
                    download_url = asset.get("browser_download_url", "")
                    api_url = asset.get("url", "")  # API URL for authenticated downloads
                    size = asset.get("size", 0)

                    if asset_name and download_url:
                        assets.append(GitHubReleaseService.AssetInfo(asset_name, download_url, size, tag_name, api_url))

            GitHubReleaseService.logger.info(f"Found {len(assets)} assets across releases")
            return assets

        except requests.RequestException as e:
            GitHubReleaseService.logger.error(f"Failed to fetch releases: {e}")
            return []

    @staticmethod
    def _download_with_progress(response, output_path, progress_callback=None, should_cancel=None):
        """Download file with progress tracking."""
        GitHubReleaseService.logger.info(f"Starting download to: {output_path}")
        total_size = int(response.headers.get("content-length", 0))
        with open(output_path, "wb") as f:
            downloaded = 0
            last_percent = -1
            for chunk in response.iter_content(chunk_size=8192):
                if should_cancel and should_cancel():
                    GitHubReleaseService.logger.info("Download cancelled by user.")
                    break
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        percent_int = int(percent)
                        # Only call progress_callback if percent changed
                        if progress_callback and percent_int != last_percent:
                            # Enhanced progress callback with byte information
                            progress_callback(percent, downloaded, total_size)
                            last_percent = percent_int
                    elif progress_callback:
                        # Fallback when total_size is unknown
                        percent = 0
                        progress_callback(percent, downloaded, 0)
        GitHubReleaseService.logger.info(f"\nDownloaded successfully to: {output_path}")

    @staticmethod
    def download_asset(
        asset_url: str, output_path: str, progress_callback=None, should_cancel=None, api_url: str = None
    ) -> bool:
        """
        Download an asset from its URL.

        Args:
            asset_url: Direct download URL for the asset (browser URL)
            output_path: Local path to save the downloaded file
            progress_callback: Optional callback function(percent, downloaded_bytes, total_bytes)
            should_cancel: Optional function that returns True if download should be cancelled
            api_url: Optional API URL for authenticated downloads (used for private repos)

        Returns:
            True if download was successful, False otherwise
        """
        headers = GitHubReleaseService._get_headers()

        try:
            # For private repositories, use the API URL with Accept header for octet-stream
            # For public repositories, the browser download URL works fine
            if api_url and os.environ.get("GITHUB_TOKEN"):
                # Use API endpoint for authenticated download
                headers["Accept"] = "application/octet-stream"
                url_to_use = api_url
                GitHubReleaseService.logger.debug(f"Using API URL for authenticated download: {api_url}")
            else:
                url_to_use = asset_url
                GitHubReleaseService.logger.debug(f"Using browser URL for download: {asset_url}")

            response = requests.get(url_to_use, headers=headers, stream=True, timeout=30, allow_redirects=True)

            if response.status_code == 404:
                GitHubReleaseService.logger.error(
                    f"Asset not found: {url_to_use}\n"
                    "This could mean:\n"
                    "  1. The asset was deleted or renamed\n"
                    "  2. For private repositories: Ensure GITHUB_TOKEN is set with 'repo' scope\n"
                    "  3. The token may not have permission to download release assets"
                )
                return False

            if response.status_code == 401 or response.status_code == 403:
                GitHubReleaseService.logger.error(
                    f"Authentication failed (HTTP {response.status_code})\n"
                    "Please check:\n"
                    "  1. GITHUB_TOKEN is set correctly\n"
                    "  2. Token has 'repo' scope for private repositories\n"
                    "  3. Token has not expired"
                )
                return False

            response.raise_for_status()

            GitHubReleaseService._download_with_progress(response, output_path, progress_callback, should_cancel)
            return True

        except requests.RequestException as e:
            GitHubReleaseService.logger.error(f"[Error] Download failed: {e}")
            return False

    @staticmethod
    def get_latest_for_platform(
        assets: List["GitHubReleaseService.AssetInfo"],
        platform: str,
    ) -> Optional["GitHubReleaseService.AssetInfo"]:
        """
        Get the latest version for the specified platform (extension).

        Args:
            assets: List of AssetInfo objects
            platform: Platform extension (dmg, msi, flatpak)

        Returns:
            AssetInfo for the latest version of the specified platform, or None
        """
        latest_asset = None
        for asset in assets:
            if asset.version is not None and asset.extension == platform:
                if latest_asset is None or asset.version > latest_asset.version:
                    latest_asset = asset
        return latest_asset

    @staticmethod
    def get_latest_by_platform(
        assets: List["GitHubReleaseService.AssetInfo"],
    ) -> dict[str, "GitHubReleaseService.AssetInfo"]:
        """
        Get the latest version for each platform.

        Args:
            assets: List of AssetInfo objects

        Returns:
            Dictionary mapping platform extension to latest AssetInfo
        """
        platforms = ["dmg", "msi", "flatpak"]
        latest_by_platform = {}

        for platform in platforms:
            latest = GitHubReleaseService.get_latest_for_platform(assets, platform)
            if latest:
                latest_by_platform[platform] = latest

        return latest_by_platform

    @staticmethod
    def get_platform_for_os() -> str:
        """
        Returns the platform extension for the current operating system.

        Returns:
            Platform string: "dmg" for macOS, "msi" for Windows, "flatpak" for Linux

        Raises:
            RuntimeError: If the operating system is not recognized
        """
        os_name = py_platform.system().lower()
        if os_name == "darwin":
            return "dmg"
        elif os_name == "windows":
            return "msi"
        elif os_name == "linux":
            return "flatpak"

        raise RuntimeError(f"Unknown operating system {os_name}")

    @staticmethod
    def is_asset_newer_than_version(asset_info: "GitHubReleaseService.AssetInfo", version: str) -> bool:
        """
        Returns True if the asset's version is newer than the indicated version.

        Args:
            asset_info: AssetInfo object to check
            version: Version string to compare against

        Returns:
            True if asset version is newer, False otherwise
        """
        if asset_info.version is None:
            return False
        try:
            compare_version = Version(version)
            return asset_info.version > compare_version
        except InvalidVersion:
            return False
