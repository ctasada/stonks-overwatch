import os
import signal
import sys

from django.apps import AppConfig

from stonks_overwatch.utils.logger import StonksLogger

class StonksOverwatchConfig(AppConfig):
    logger = StonksLogger.get_logger("stonks_overwatch.config", "[MAIN]")
    default_auto_field = "django.db.models.BigAutoField"
    name = "stonks_overwatch"

    def ready(self):
        # Guarantee that the Jobs are initialized only once
        if os.environ.get('RUN_MAIN'):
            self.logger.info("Stonks Overwatch ready - RUN MAIN")
            self.show_env_vars()

            signal.signal(signal.SIGINT, self.handle_shutdown)
            signal.signal(signal.SIGTERM, self.handle_shutdown)

            # Schedule automatic tasks
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler
            JobsScheduler.start()

    def show_env_vars(self):
        debug_mode = os.getenv("DEBUG_MODE", False) in [True, "true", "True", "1"]
        if debug_mode:
            self.logger.info("Enabling DEBUG_MODE: %s", debug_mode)
        profile_mode = os.getenv("PROFILE_MODE", False) in [True, "true", "True", "1"]
        if profile_mode:
            self.logger.info("Enabling PROFILE_MODE: %s", profile_mode)
        demo_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]
        if demo_mode:
            self.logger.info("Using DEMO database: %s", profile_mode)

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
