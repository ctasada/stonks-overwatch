import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from packaging.version import InvalidVersion, Version

from stonks_overwatch.utils.core.logger import StonksLogger


class GoogleDriveService:
    logger = StonksLogger.get_logger("stonks_overwatch.google_drive_service", "[GOOGLE_DRIVE|SERVICE]")

    # The Google Drive folder is https://drive.google.com/drive/folders/1riC-45oXY70v4pHpvmCx1YLpVmfiupNf
    DEFAULT_FOLDER_ID = "1riC-45oXY70v4pHpvmCx1YLpVmfiupNf"

    class FileInfo:
        def __init__(self, name: str, file_id: str) -> None:
            self.name: str = name
            self.id: str = file_id
            self.version: Optional[Version] = self.extract_version()
            self.extension: Optional[str] = self.extract_extension()

        def extract_version(self) -> Optional[Version]:
            # Support both Stonks.Overwatch-0.1.0 and Stonks_Overwatch-0.1.0-x86_64
            match = re.search(r"Stonks[._]Overwatch-([0-9]+\.[0-9]+\.[0-9]+)", self.name)
            if match:
                try:
                    return Version(match.group(1))
                except InvalidVersion:
                    return None
            return None

        def extract_extension(self) -> Optional[str]:
            # Extract extension at the end, e.g. .dmg, .msi, .flatpak
            match = re.search(r"\.(dmg|msi|flatpak)$", self.name)
            if match:
                return match.group(1)
            return None

        def __repr__(self) -> str:
            return f"FileInfo(name={self.name}, id={self.id}, version={self.version}, ext={self.extension})"

    @staticmethod
    def list_files(folder_id: str = DEFAULT_FOLDER_ID) -> List["GoogleDriveService.FileInfo"]:
        url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        files = []
        for a in soup.find_all("a"):
            name = a.text.strip()
            href = a.get("href", "")
            if href.startswith("https://drive.google.com/file/d/"):
                parts = href.split("/d/")
                if len(parts) > 1:
                    file_id = parts[1].split("/")[0]
                    files.append(GoogleDriveService.FileInfo(name, file_id))
        return files

    @staticmethod
    def _handle_virus_scan(session, response):
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form", {"id": "download-form"})
        if not form:
            GoogleDriveService.logger.error("[Error] Could not find download form in warning page")
            GoogleDriveService.logger.error("Response snippet:", response.text[:500])
            return None
        action_url = form.get("action")
        if not action_url:
            GoogleDriveService.logger.error("[Error] Could not find form action URL")
            return None
        params = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value")
            if name and value:
                params[name] = value
        GoogleDriveService.logger.debug(f"Extracted parameters: {list(params.keys())}")
        return session.get(action_url, params=params, stream=True)

    @staticmethod
    def _download_with_progress(response, output_path):
        GoogleDriveService.logger.info(f"Starting download to: {output_path}")
        total_size = int(response.headers.get("content-length", 0))
        with open(output_path, "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end="", flush=True)
        GoogleDriveService.logger.info(f"\nDownloaded successfully to: {output_path}")

    @staticmethod
    def download_file(file_id: str, output_path: str) -> bool:
        session = requests.Session()
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        try:
            response = session.get(download_url, stream=True)
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                GoogleDriveService.logger.info("Got virus scan warning page, extracting download parameters...")
                response = GoogleDriveService._handle_virus_scan(session, response)
                if response is None:
                    return False
            response.raise_for_status()
            final_content_type = response.headers.get("content-type", "")
            if "text/html" in final_content_type:
                GoogleDriveService.logger.error("[Error] Still getting HTML response, download failed")
                GoogleDriveService.logger.error("Response content:", response.text[:500])
                return False
            GoogleDriveService._download_with_progress(response, output_path)
            return True
        except Exception as e:
            GoogleDriveService.logger.error(f"[Error] Download failed: {e}")
            return False

    @staticmethod
    def get_latest_for_platform(
        files: List["GoogleDriveService.FileInfo"],
        platform: str,
    ) -> Optional["GoogleDriveService.FileInfo"]:
        """
        Get the latest version for the specified platform (extension)
        """
        latest_file = None
        for f in files:
            if f.version is not None and f.extension == platform:
                if latest_file is None or f.version > latest_file.version:
                    latest_file = f
        return latest_file
