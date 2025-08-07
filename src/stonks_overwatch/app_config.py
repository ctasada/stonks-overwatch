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
                from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
                from stonks_overwatch.core.registry_setup import register_all_brokers

                # Check if brokers are already registered to avoid duplicates
                registry = BrokerRegistry()
                registered_brokers = registry.get_fully_registered_brokers()

                if not registered_brokers:
                    # No brokers registered yet, proceed with registration
                    register_all_brokers()
                    self.logger.info("Broker services registered successfully")
                else:
                    # Brokers already registered (likely through automatic initialization)
                    self.logger.info(f"Broker services already registered: {registered_brokers}")
            except Exception as e:
                self.logger.error("Failed to register broker services: %s", e)
                # Legacy fallback removed - unified registry setup is now the only option
                raise e

            # Register authentication services with dependency injection
            try:
                from stonks_overwatch.core.authentication_locator import AuthenticationServiceLocator
                from stonks_overwatch.core.authentication_setup import register_authentication_services
                from stonks_overwatch.core.factories.authentication_factory import AuthenticationFactory

                # Check if authentication services are already registered to avoid duplicates
                auth_factory = AuthenticationFactory()

                if not auth_factory.is_fully_registered():
                    # No authentication services registered yet, proceed with registration
                    register_authentication_services()
                    self.logger.info("Authentication services registered successfully")
                else:
                    # Authentication services already registered
                    registered_services = auth_factory.get_registered_services()
                    self.logger.info(f"Authentication services already registered: {registered_services}")

                # Warm up authentication service cache for optimal performance
                AuthenticationServiceLocator.warmup_cache()
                cache_status = AuthenticationServiceLocator.get_cache_status()
                self.logger.info(f"Authentication service cache warmed up: {cache_status}")

            except Exception as e:
                self.logger.error("Failed to register authentication services: %s", e)
                raise e

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

        # Clear authentication service cache to free memory
        try:
            from stonks_overwatch.core.authentication_locator import clear_authentication_cache

            clear_authentication_cache()
            self.logger.info("Stonks Overwatch - Cleared authentication service cache")
        except Exception as e:
            self.logger.error(f"Failed to clear authentication cache: {e}")

        self.logger.info("Stonks Overwatch - Closing connections")
        from stonks_overwatch.services.ibkr.ibkr_service import IbkrService

        IbkrService().get_client().oauth_shutdown()
        self.logger.info("Stonks Overwatch - Connections closed")
