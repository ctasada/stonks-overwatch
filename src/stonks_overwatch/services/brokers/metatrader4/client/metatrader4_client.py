from typing import Optional

import paramiko

from stonks_overwatch.config.metatrader4 import Metatrader4Config
from stonks_overwatch.utils.core.logger import StonksLogger


class Metatrader4Client:
    def __init__(self, config: Metatrader4Config):
        self.config = config
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|CLIENT]")

    def get_report_content(self) -> Optional[str]:
        """Retrieve content from SFTP server using configuration."""
        try:
            credentials = self.config.get_credentials

            if not credentials or not credentials.has_minimal_credentials():
                self.logger.error("MetaTrader 4 credentials missing or incomplete in configuration.")
                raise ValueError("Metatrader4 credentials missing or incomplete")

            self.logger.info(f"Connecting to SFTP server: {credentials.ftp_server}")

            # Use SFTP for secure file transfer
            with paramiko.SSHClient() as ssh_client:
                # Configure SSH client security
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to server with explicit port (default 22 for SFTP)
                port = 22  # SFTP standard port
                ssh_client.connect(
                    hostname=credentials.ftp_server,
                    port=port,
                    username=credentials.username,
                    password=credentials.password,
                    timeout=30,
                )

                # Open SFTP session
                with ssh_client.open_sftp() as sftp_client:
                    self.logger.info(f"Downloading file via SFTP: {credentials.path}")

                    # Read file content
                    with sftp_client.open(credentials.path, "rb") as remote_file:
                        content = remote_file.read()

                    # Decode content with error handling
                    try:
                        decoded_content = content.decode("utf-8")
                    except UnicodeDecodeError:
                        self.logger.warning("UTF-8 decode failed, using error handling")
                        decoded_content = content.decode("utf-8", errors="ignore")

                    self.logger.info("File retrieved successfully via SFTP")
                    return decoded_content

        except Exception as e:
            self.logger.exception(f"Failed to retrieve file from SFTP server: {e}")
            raise
