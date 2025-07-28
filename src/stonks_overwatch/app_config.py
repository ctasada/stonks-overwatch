import os
import sys

from django.apps import AppConfig

from stonks_overwatch.utils.core.logger import StonksLogger


class StonksOverwatchConfig(AppConfig):
    logger = StonksLogger.get_logger("stonks_overwatch.config", "[MAIN]")
    default_auto_field = "django.db.models.BigAutoField"
    name = "stonks_overwatch"

    def ready(self):
        # Guarantee that the Jobs are initialized only once
        if os.environ.get("RUN_MAIN") or os.environ.get("STONKS_OVERWATCH_APP"):
            self.logger.info("Stonks Overwatch ready - RUN MAIN")
            self.show_env_vars()

            if os.environ.get("RUN_MAIN"):
                # FIXME: An equivalent is needed when running the app in production
                import signal

                signal.signal(signal.SIGINT, self.handle_shutdown)
                signal.signal(signal.SIGTERM, self.handle_shutdown)

            # Register broker services with the unified framework
            try:
                from stonks_overwatch.core.unified_registry_setup import register_all_brokers

                register_all_brokers()
                self.logger.info("Unified broker services registered successfully")
            except Exception as e:
                self.logger.error("Failed to register unified broker services: %s", e)
                # Fallback to legacy registration for backward compatibility
                # try:
                #     from stonks_overwatch.core.registry_setup import register_broker_services
                #     register_broker_services()
                #     self.logger.info("Legacy broker services registered as fallback")
                # except Exception as fallback_e:
                #     self.logger.error("Failed to register legacy broker services: %s", fallback_e)

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

        self.logger.info("Stonks Overwatch - Closing connections")
        from stonks_overwatch.services.ibkr.ibkr_service import IbkrService

        IbkrService().get_client().oauth_shutdown()
        self.logger.info("Stonks Overwatch - Connections closed")
