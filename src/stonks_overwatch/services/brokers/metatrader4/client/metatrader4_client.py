import ftplib
from io import BytesIO
from typing import Optional

from stonks_overwatch.config.metatrader4 import Metatrader4Config
from stonks_overwatch.utils.core.logger import StonksLogger


class Metatrader4Client:
    def __init__(self, config: Metatrader4Config):
        self.config = config
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|CLIENT]")

    def get_report_content(self) -> Optional[str]:
        """Retrieve content from FTP server using configuration."""
        try:
            credentials = self.config.get_credentials

            if not credentials or not credentials.has_minimal_credentials():
                self.logger.error("MetaTrader 4 credentials missing or incomplete in configuration.")
                raise ValueError("Metatrader4 credentials missing or incomplete")

            self.logger.info(f"Connecting to FTP server: {credentials.ftp_server}")

            # Connect to FTP
            with ftplib.FTP(credentials.ftp_server) as ftp:
                ftp.login(user=credentials.username, passwd=credentials.password)

                # Retrieve file
                self.logger.info(f"Downloading file: {credentials.path}")

                # Using BytesIO to store file in memory
                file_buffer = BytesIO()
                ftp.retrbinary(f"RETR {credentials.path}", file_buffer.write)

            # Decode content
            file_buffer.seek(0)
            # Try appropriate encodings
            content = file_buffer.read().decode("utf-8", errors="ignore")
            self.logger.info("File retrieved successfully.")
            return content

        except Exception as e:
            self.logger.exception(f"Failed to retrieve file from FTP: {e}")
            raise
