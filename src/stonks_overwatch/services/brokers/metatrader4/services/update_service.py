from typing import Optional

from stonks_overwatch.config.metatrader4 import Metatrader4Config
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.metatrader4.client.metatrader4_client import Metatrader4Client
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.brokers.metatrader4.utilities.parser import parse_mt4_html
from stonks_overwatch.utils.core.logger import StonksLogger


class UpdateService(BaseService, AbstractUpdateService):
    """
    Metatrader4 Update Service.

    This service handles the scheduled fetching and storing of MT4 data.
    It downloads HTML reports from FTP, parses them, and stores the data
    in the database for historical tracking and analysis.
    """

    def __init__(
        self,
        import_folder: Optional[str] = None,
        debug_mode: Optional[bool] = None,
        config: Optional[Metatrader4Config] = None,
    ):
        """
        Initialize the MT4 UpdateService.

        Args:
            import_folder: Folder to store JSON files for debugging purposes
            debug_mode: If True, the service will store JSON files for debugging
            config: Optional MT4 configuration instance for dependency injection
        """
        # Initialize AbstractUpdateService first
        AbstractUpdateService.__init__(self, BrokerName.METATRADER4, import_folder, debug_mode, config)

        # Then manually set BaseService attributes without calling its __init__
        self._global_config = None
        self._injected_config = config

        if self._injected_config is None:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            self._injected_config = broker_factory.create_config(BrokerName.METATRADER4)

        # Initialize MT4 components
        self.client = Metatrader4Client(self._injected_config)
        self.repository = Metatrader4Repository()

        # Create a mock service attribute for the job scheduler pattern
        self.mt4_service = self

        # Override logger with MT4-specific prefix
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|UPDATE]")

    def update_all(self):
        """
        Update all MT4 data by fetching, parsing, and storing the latest report.

        This method:
        1. Downloads the HTML report from the configured FTP server
        2. Parses the HTML content to extract structured data
        3. Stores the parsed data in the database
        4. Handles errors gracefully and logs progress
        """
        self.logger.info("Starting MT4 data update")

        try:
            # Check if MT4 is enabled and configured
            if not self._injected_config or not self._injected_config.is_enabled():
                self.logger.warning("MetaTrader 4 is not enabled, skipping update")
                return

            credentials = self._injected_config.get_credentials
            if not credentials or not credentials.has_minimal_credentials():
                self.logger.error("MetaTrader 4 credentials missing or incomplete, skipping update")
                return

            # Download HTML report from FTP
            self.logger.info("Downloading MT4 report from FTP server")
            html_content = self.client.get_report_content()

            if not html_content:
                self.logger.warning("No HTML content received from FTP server")
                return

            # Parse the HTML content
            self.logger.info("Parsing MT4 HTML report")
            parse_result = parse_mt4_html(html_content)

            # Log parsing results
            self.logger.info(
                f"Parsed MT4 report: {len(parse_result.closed_transactions)} closed transactions, "
                f"{len(parse_result.open_trades)} open trades, "
                f"{len(parse_result.working_orders)} working orders"
            )

            # Store debug files if enabled
            if self.debug_mode:
                self._save_debug_files(parse_result, html_content)

            # Store parsed data in database
            self.logger.info("Storing parsed data in database using optimized upsert strategy")

            success = self.repository.store_parsed_report(parse_result=parse_result, file_path=credentials.path)

            if success:
                self.logger.info("Successfully stored MT4 report data")

                # Perform periodic cleanup (every 10th update to avoid overhead)
                import random

                if random.randint(1, 10) == 1:  # 10% chance
                    self.logger.debug("Performing periodic cleanup of orphaned trades")
                    cleaned_count = self.repository.cleanup_orphaned_trades()
                    if cleaned_count > 0:
                        self.logger.info(f"Cleaned up {cleaned_count} orphaned records during periodic maintenance")
            else:
                self.logger.warning("Failed to store MT4 report data")

        except Exception as e:
            self.logger.error(f"MT4 update failed: {e}", exc_info=True)
            raise

    def _save_debug_files(self, parse_result, html_content: str):
        """Save debug files when debug mode is enabled."""
        import os

        from stonks_overwatch.utils.core.debug import save_to_json

        try:
            # Save raw HTML content
            html_file = os.path.join(self.import_folder, "mt4_report.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Save parsed data as JSON
            parsed_file = os.path.join(self.import_folder, "mt4_parsed.json")
            save_to_json(parse_result.to_dict(), parsed_file)

            # Save individual sections
            if parse_result.closed_transactions:
                closed_file = os.path.join(self.import_folder, "mt4_closed_transactions.json")
                save_to_json(parse_result.closed_transactions, closed_file)

            if parse_result.open_trades:
                open_file = os.path.join(self.import_folder, "mt4_open_trades.json")
                save_to_json(parse_result.open_trades, open_file)

            if parse_result.working_orders:
                orders_file = os.path.join(self.import_folder, "mt4_working_orders.json")
                save_to_json(parse_result.working_orders, orders_file)

            if parse_result.summary:
                summary_file = os.path.join(self.import_folder, "mt4_summary.json")
                save_to_json(parse_result.summary, summary_file)

            self.logger.debug(f"Debug files saved to {self.import_folder}")

        except Exception as e:
            self.logger.warning(f"Failed to save debug files: {e}")

    def get_client(self):
        """
        Get the MT4 client for connection checking.

        Returns:
            Metatrader4Client: The FTP client instance
        """
        return self.client

    def get_last_import(self):
        """
        Get the timestamp of the last successful import.

        Returns:
            datetime: The timestamp of the most recent trade update
        """
        latest_trade = self.repository.get_latest_trades(limit=1)
        if latest_trade:
            return latest_trade[0].created_at

        # Fallback to config start date if no trades exist
        if self._injected_config and hasattr(self._injected_config, "start_date"):
            from datetime import datetime, time

            return datetime.combine(self._injected_config.start_date, time.min)

        # Final fallback
        from datetime import datetime, timedelta

        return datetime.now() - timedelta(days=30)
