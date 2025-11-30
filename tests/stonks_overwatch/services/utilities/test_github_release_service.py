"""
Unit tests for GitHubReleaseService.
"""

from packaging.version import Version

from stonks_overwatch.services.utilities.github_release_service import GitHubReleaseService

import pook
import pytest


class TestGitHubReleaseService:
    def make_asset(self, name, download_url, size, release_tag, api_url=None):
        return GitHubReleaseService.AssetInfo(name, download_url, size, release_tag, api_url)

    def test_get_latest_for_platform(self):
        assets = [
            self.make_asset("Stonks.Overwatch-0.1.0.dmg", "https://example.com/1", 1000, "v0.1.0"),
            self.make_asset("Stonks.Overwatch-0.2.0.dmg", "https://example.com/2", 1000, "v0.2.0"),
            self.make_asset("Stonks.Overwatch-0.2.0-macos.dmg", "https://example.com/2b", 1000, "v0.2.0"),
            self.make_asset("Stonks.Overwatch-0.1.0.msi", "https://example.com/3", 1000, "v0.1.0"),
            self.make_asset("Stonks.Overwatch-0.3.0.msi", "https://example.com/4", 1000, "v0.3.0"),
            self.make_asset("Stonks.Overwatch-0.3.0-windows.msi", "https://example.com/4b", 1000, "v0.3.0"),
            self.make_asset("Stonks.Overwatch-0.2.0.flatpak", "https://example.com/5", 1000, "v0.2.0"),
            self.make_asset("Stonks.Overwatch-0.4.0-linux.flatpak", "https://example.com/6", 1000, "v0.4.0"),
        ]
        latest_dmg = GitHubReleaseService.get_latest_for_platform(assets, "dmg")
        latest_msi = GitHubReleaseService.get_latest_for_platform(assets, "msi")
        latest_flatpak = GitHubReleaseService.get_latest_for_platform(assets, "flatpak")
        assert latest_dmg.version == Version("0.2.0")
        assert latest_dmg.name in ("Stonks.Overwatch-0.2.0.dmg", "Stonks.Overwatch-0.2.0-macos.dmg")
        assert latest_msi.version == Version("0.3.0")
        assert latest_msi.name in ("Stonks.Overwatch-0.3.0.msi", "Stonks.Overwatch-0.3.0-windows.msi")
        assert latest_flatpak.version == Version("0.4.0")
        assert latest_flatpak.name == "Stonks.Overwatch-0.4.0-linux.flatpak"

    def test_get_latest_for_platform_empty(self):
        assets = [self.make_asset("randomfile.txt", "https://example.com/1", 1000, "v1.0.0")]
        latest = GitHubReleaseService.get_latest_for_platform(assets, "dmg")
        assert latest is None

    def test_get_latest_by_platform(self):
        assets = [
            self.make_asset("Stonks.Overwatch-0.2.0.dmg", "https://example.com/1", 1000, "v0.2.0"),
            self.make_asset("Stonks.Overwatch-0.3.0.msi", "https://example.com/2", 1000, "v0.3.0"),
            self.make_asset("Stonks.Overwatch-0.4.0.flatpak", "https://example.com/3", 1000, "v0.4.0"),
        ]
        latest_by_platform = GitHubReleaseService.get_latest_by_platform(assets)
        assert len(latest_by_platform) == 3
        assert latest_by_platform["dmg"].version == Version("0.2.0")
        assert latest_by_platform["msi"].version == Version("0.3.0")
        assert latest_by_platform["flatpak"].version == Version("0.4.0")

    @pook.on
    def test_list_releases_success(self):
        mock_response = [
            {
                "tag_name": "v0.1.0",
                "prerelease": False,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.1.0.dmg",
                        "browser_download_url": "https://github.com/releases/download/v0.1.0/file.dmg",
                        "size": 10000000,
                    }
                ],
            },
            {
                "tag_name": "v0.2.0",
                "prerelease": False,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.2.0.msi",
                        "browser_download_url": "https://github.com/releases/download/v0.2.0/file.msi",
                        "size": 15000000,
                    }
                ],
            },
        ]
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            response_json=mock_response,
            status=200,
        )
        assets = GitHubReleaseService.list_releases()
        assert len(assets) == 2
        assert assets[0].name == "Stonks.Overwatch-0.1.0.dmg"
        assert assets[0].version == Version("0.1.0")
        assert assets[0].extension == "dmg"
        assert assets[1].name == "Stonks.Overwatch-0.2.0.msi"
        assert assets[1].extension == "msi"

    @pook.on
    def test_list_releases_skip_prereleases(self):
        mock_response = [
            {
                "tag_name": "v0.1.0",
                "prerelease": False,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.1.0.dmg",
                        "browser_download_url": "https://github.com/releases/download/v0.1.0/file.dmg",
                        "size": 10000000,
                    }
                ],
            },
            {
                "tag_name": "v0.2.0-beta",
                "prerelease": True,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.2.0-beta.msi",
                        "browser_download_url": "https://github.com/releases/download/v0.2.0-beta/file.msi",
                        "size": 15000000,
                    }
                ],
            },
        ]
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            response_json=mock_response,
            status=200,
        )
        assets = GitHubReleaseService.list_releases(include_prereleases=False)
        assert len(assets) == 1
        assert assets[0].name == "Stonks.Overwatch-0.1.0.dmg"

    @pook.on
    def test_list_releases_include_prereleases(self):
        mock_response = [
            {
                "tag_name": "v0.1.0",
                "prerelease": False,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.1.0.dmg",
                        "browser_download_url": "https://github.com/releases/download/v0.1.0/file.dmg",
                        "size": 10000000,
                    }
                ],
            },
            {
                "tag_name": "v0.2.0-beta",
                "prerelease": True,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.2.0-beta.msi",
                        "browser_download_url": "https://github.com/releases/download/v0.2.0-beta/file.msi",
                        "size": 15000000,
                    }
                ],
            },
        ]
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            response_json=mock_response,
            status=200,
        )
        assets = GitHubReleaseService.list_releases(include_prereleases=True)
        assert len(assets) == 2

    @pook.on
    def test_list_releases_skip_drafts(self):
        mock_response = [
            {
                "tag_name": "v0.1.0",
                "prerelease": False,
                "draft": False,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.1.0.dmg",
                        "browser_download_url": "https://github.com/releases/download/v0.1.0/file.dmg",
                        "size": 10000000,
                    }
                ],
            },
            {
                "tag_name": "v0.2.0-draft",
                "prerelease": False,
                "draft": True,
                "assets": [
                    {
                        "name": "Stonks.Overwatch-0.2.0-draft.msi",
                        "browser_download_url": "https://github.com/releases/download/v0.2.0-draft/file.msi",
                        "size": 15000000,
                    }
                ],
            },
        ]
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            response_json=mock_response,
            status=200,
        )
        assets = GitHubReleaseService.list_releases()
        assert len(assets) == 1
        assert assets[0].name == "Stonks.Overwatch-0.1.0.dmg"

    @pook.on
    def test_list_releases_empty(self):
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            response_json=[],
            status=200,
        )
        assets = GitHubReleaseService.list_releases()
        assert assets == []

    @pook.on
    def test_list_releases_http_error(self):
        pook.get(
            "https://api.github.com/repos/ctasada/stonks-overwatch/releases",
            status=404,
        )
        assets = GitHubReleaseService.list_releases()
        assert assets == []

    @pook.on
    def test_download_asset_success(self, tmp_path):
        download_url = "https://github.com/releases/download/v0.1.0/file.dmg"
        output_path = tmp_path / "test.dmg"
        file_content = b"dummy file content"
        pook.get(
            download_url,
            response_body=file_content,
            reply_headers={"content-type": "application/octet-stream", "content-length": str(len(file_content))},
            status=200,
        )
        result = GitHubReleaseService.download_asset(download_url, str(output_path))
        assert result is True
        assert output_path.read_bytes() == file_content

    @pook.on
    def test_download_asset_http_error(self, tmp_path):
        download_url = "https://github.com/releases/download/v0.1.0/file.dmg"
        output_path = tmp_path / "test.dmg"
        pook.get(
            download_url,
            status=404,
        )
        result = GitHubReleaseService.download_asset(download_url, str(output_path))
        assert result is False

    def test_get_platform_for_os(self, monkeypatch):
        # Test for macOS
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        assert GitHubReleaseService.get_platform_for_os() == "dmg"
        # Test for Windows
        monkeypatch.setattr("platform.system", lambda: "Windows")
        assert GitHubReleaseService.get_platform_for_os() == "msi"
        # Test for Linux
        monkeypatch.setattr("platform.system", lambda: "Linux")
        assert GitHubReleaseService.get_platform_for_os() == "flatpak"
        # Test for unknown OS
        monkeypatch.setattr("platform.system", lambda: "Solaris")
        with pytest.raises(RuntimeError):
            GitHubReleaseService.get_platform_for_os()

    def test_assetinfo_version_from_tag(self):
        # Test version parsing from release tag
        asset1 = self.make_asset("Stonks.Overwatch.dmg", "https://example.com/1", 1000, "v1.2.3")
        asset2 = self.make_asset("Stonks.Overwatch.msi", "https://example.com/2", 1000, "2.0.0")
        assert asset1.version == Version("1.2.3")
        assert asset2.version == Version("2.0.0")

    def test_assetinfo_version_from_filename(self):
        # Test version parsing from filename when tag doesn't have a version
        asset = self.make_asset("Stonks.Overwatch-1.2.3-macos.dmg", "https://example.com/1", 1000, "latest")
        assert asset.version == Version("1.2.3")

    def test_assetinfo_parsing_with_os_suffix(self):
        # Test version and extension parsing for files with OS/arch suffix
        asset1 = self.make_asset("Stonks.Overwatch-1.2.3-macos.dmg", "https://example.com/1", 1000, "v1.2.3")
        asset2 = self.make_asset("Stonks.Overwatch-2.0.0-windows.msi", "https://example.com/2", 1000, "v2.0.0")
        asset3 = self.make_asset("Stonks.Overwatch-3.1.4-linux.flatpak", "https://example.com/3", 1000, "v3.1.4")
        assert asset1.version == Version("1.2.3")
        assert asset1.extension == "dmg"
        assert asset2.version == Version("2.0.0")
        assert asset2.extension == "msi"
        assert asset3.version == Version("3.1.4")
        assert asset3.extension == "flatpak"

    def test_is_asset_newer_than_version(self):
        # Newer version
        asset_newer = self.make_asset("Stonks.Overwatch-0.2.0.dmg", "https://example.com/1", 1000, "v0.2.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_newer, "0.1.0") is True
        # Newer version with OS in filename
        asset_newer_os = self.make_asset("Stonks.Overwatch-0.2.0-macos.dmg", "https://example.com/1b", 1000, "v0.2.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_newer_os, "0.1.0") is True
        # Same version
        asset_same = self.make_asset("Stonks.Overwatch-0.1.0.dmg", "https://example.com/2", 1000, "v0.1.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_same, "0.1.0") is False
        # Same version with OS in filename
        asset_same_os = self.make_asset("Stonks.Overwatch-0.1.0-windows.msi", "https://example.com/2b", 1000, "v0.1.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_same_os, "0.1.0") is False
        # Older version
        asset_older = self.make_asset("Stonks.Overwatch-0.1.0.dmg", "https://example.com/3", 1000, "v0.1.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_older, "0.2.0") is False
        # Older version with OS in filename
        asset_older_os = self.make_asset(
            "Stonks.Overwatch-0.1.0-linux.flatpak", "https://example.com/3b", 1000, "v0.1.0"
        )
        assert GitHubReleaseService.is_asset_newer_than_version(asset_older_os, "0.2.0") is False
        # Invalid filename (no version)
        asset_invalid = self.make_asset("randomfile.txt", "https://example.com/4", 1000, "latest")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_invalid, "0.1.0") is False
        # Invalid version string
        asset_valid = self.make_asset("Stonks.Overwatch-0.2.0.dmg", "https://example.com/5", 1000, "v0.2.0")
        assert GitHubReleaseService.is_asset_newer_than_version(asset_valid, "not_a_version") is False
