import os
import signal
import sys

from django.apps import AppConfig

from stonks_overwatch.utils.logger import StonksLogger


class StonksOverwatchConfig(AppConfig):
    logger = StonksLogger.get_logger("stocks_portfolio.config", "[MAIN]")
    default_auto_field = "django.db.models.BigAutoField"
    name = "stonks_overwatch"

    def ready(self):
        # Guarantee that the Jobs are initialized only once
        if os.environ.get('RUN_MAIN'):
            self.logger.info("Stonks Overwatch ready - RUN MAIN")
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            signal.signal(signal.SIGINT, self.handle_shutdown)
            signal.signal(signal.SIGTERM, self.handle_shutdown)

            # Schedule automatic tasks
            JobsScheduler.start()

    def handle_shutdown(self, signum, frame):
        try:
            # Close your connections here
            self.close_connections()
        finally:
            sys.exit(0)

    def close_connections(self):
        # Ensure scheduler is shut down properly
        from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler
        self.logger.info("Stonks Overwatch - Stopping JobsScheduler")
        JobsScheduler.stop()
