"""
Unit tests for GoogleDriveService.
"""

import requests
from packaging.version import Version

from stonks_overwatch.services.utilities.google_drive_service import GoogleDriveService

import pook
import pytest


class TestGoogleDriveService:
    def make_file(self, name, file_id):
        return GoogleDriveService.FileInfo(name, file_id)

    def test_get_latest_for_platform(self):
        files = [
            self.make_file("Stonks.Overwatch-0.1.0.dmg", "1"),
            self.make_file("Stonks.Overwatch-0.2.0.dmg", "2"),
            self.make_file("Stonks.Overwatch-0.1.0.msi", "3"),
            self.make_file("Stonks.Overwatch-0.3.0.msi", "4"),
            self.make_file("Stonks.Overwatch-0.2.0.flatpak", "5"),
        ]
        latest_dmg = GoogleDriveService.get_latest_for_platform(files, "dmg")
        latest_msi = GoogleDriveService.get_latest_for_platform(files, "msi")
        latest_flatpak = GoogleDriveService.get_latest_for_platform(files, "flatpak")
        assert latest_dmg.version == Version("0.2.0")
        assert latest_msi.version == Version("0.3.0")
        assert latest_flatpak.version == Version("0.2.0")

    def test_get_latest_for_platform_empty(self):
        files = [self.make_file("randomfile.txt", "1")]
        latest = GoogleDriveService.get_latest_for_platform(files, "dmg")
        assert latest is None

    @pook.on
    def test_list_files_success(self):
        html = """<html><body>
            <a href="https://drive.google.com/file/d/abc123/view">Stonks.Overwatch-0.1.0.dmg</a>
            <a href="https://drive.google.com/file/d/def456/view">Stonks.Overwatch-0.2.0.msi</a>
            <a href="https://drive.google.com/file/d/ghi789/view">Stonks.Overwatch-0.3.0.flatpak</a>
        </body></html>"""
        pook.get(
            "https://drive.google.com/embeddedfolderview?id=1riC-45oXY70v4pHpvmCx1YLpVmfiupNf#list",
            response_body=html,
            status=200,
        )
        files = GoogleDriveService.list_files()
        assert len(files) == 3
        assert files[0].name == "Stonks.Overwatch-0.1.0.dmg"
        assert files[1].id == "def456"
        assert files[2].extension == "flatpak"

    @pook.on
    def test_list_files_empty(self):
        html = "<html><body></body></html>"
        pook.get(
            "https://drive.google.com/embeddedfolderview?id=1riC-45oXY70v4pHpvmCx1YLpVmfiupNf#list",
            response_body=html,
            status=200,
        )
        files = GoogleDriveService.list_files()
        assert files == []

    @pook.on
    def test_list_files_http_error(self):
        pook.get(
            "https://drive.google.com/embeddedfolderview?id=1riC-45oXY70v4pHpvmCx1YLpVmfiupNf#list",
            status=404,
        )
        with pytest.raises(requests.HTTPError):
            GoogleDriveService.list_files()

    @pook.on
    def test_download_file_success(self, tmp_path):
        file_id = "abc123"
        output_path = tmp_path / "test.dmg"
        file_content = b"dummy file content"
        pook.get(
            f"https://drive.google.com/uc?id={file_id}&export=download",
            response_body=file_content,
            reply_headers={"content-type": "application/octet-stream", "content-length": str(len(file_content))},
            status=200,
        )
        result = GoogleDriveService.download_file(file_id, str(output_path))
        assert result is True
        assert output_path.read_bytes() == file_content

    @pook.on
    def test_download_file_virus_scan(self, tmp_path):
        file_id = "abc123"
        output_path = tmp_path / "test.dmg"
        warning_html = """<html><body>
            <form id="download-form" action="https://drive.google.com/uc?export=download">
                <input type="hidden" name="id" value="abc123" />
                <input type="hidden" name="confirm" value="t" />
            </form>
        </body></html>"""
        file_content = b"dummy file content"
        pook.get(
            f"https://drive.google.com/uc?id={file_id}&export=download",
            response_body=warning_html,
            reply_headers={"content-type": "text/html"},
            status=200,
        )
        pook.get(
            "https://drive.google.com/uc?export=download",
            response_body=file_content,
            reply_headers={"content-type": "application/octet-stream", "content-length": str(len(file_content))},
            status=200,
        )
        result = GoogleDriveService.download_file(file_id, str(output_path))
        assert result is True
        assert output_path.read_bytes() == file_content

    @pook.on
    def test_download_file_http_error(self, tmp_path):
        file_id = "abc123"
        output_path = tmp_path / "test.dmg"
        pook.get(
            f"https://drive.google.com/uc?id={file_id}&export=download",
            status=404,
        )
        result = GoogleDriveService.download_file(file_id, str(output_path))
        assert result is False

    @pook.on
    def test_download_file_virus_scan_no_form(self, tmp_path):
        file_id = "abc123"
        output_path = tmp_path / "test.dmg"
        warning_html = "<html><body>No form here</body></html>"
        pook.get(
            f"https://drive.google.com/uc?id={file_id}&export=download",
            response_body=warning_html,
            reply_headers={"content-type": "text/html"},
            status=200,
        )
        result = GoogleDriveService.download_file(file_id, str(output_path))
        assert result is False
