from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone

from stonks_overwatch.constants.brokers import BrokerName
from stonks_overwatch.core.exceptions import CredentialsException
from stonks_overwatch.services.brokers.bitvavo.services.update_service import UpdateService as BitvavoUpdateService
from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService as DegiroUpdateService
from stonks_overwatch.services.brokers.ibkr.services.update_service import UpdateService as IbkrUpdateService
from stonks_overwatch.settings import DEBUG_MODE
from stonks_overwatch.utils.core.logger import StonksLogger


class JobsScheduler:
    logger = StonksLogger.get_logger("stonks_overwatch.jobs_scheduler", "[JOB_SCHEDULER]")

    scheduler = None

    # Constants for log messages
    PROCEED_WITH_CACHED_DATA_MSG = "Proceeding with update attempt (may use cached data)"

    # Broker configuration mapping
    BROKER_CONFIGS = {
        BrokerName.DEGIRO.value: {
            "job_id": "update_degiro_portfolio",
            "check_offline": True,
            "update_service_class": DegiroUpdateService,
            "service_attr": "degiro_service",
            "connection_check": "is_connected",
            "connection_method": "connect",
        },
        BrokerName.BITVAVO.value: {
            "job_id": "update_bitvavo_portfolio",
            "check_offline": True,
            "update_service_class": BitvavoUpdateService,
            "service_attr": "bitvavo_service",
            "connection_check": "get_client",
            "connection_method": None,  # Handled during initialization
        },
        BrokerName.IBKR.value: {
            "job_id": "update_ibkr_portfolio",
            "check_offline": False,
            "update_service_class": IbkrUpdateService,
            "service_attr": "ibkr_service",
            "connection_check": "get_client",
            "connection_method": None,  # Handled during initialization
        },
    }

    @classmethod
    def get_brokers(cls):
        """Get complete broker configurations with update methods"""
        return [
            {
                "name": broker_name,
                "job_id": config["job_id"],
                "check_offline": config["check_offline"],
                "update_method": cls._create_update_method(broker_name),
            }
            for broker_name, config in cls.BROKER_CONFIGS.items()
        ]

    @classmethod
    def _create_update_method(cls, broker_name: BrokerName):
        """Create a generic update method for a specific broker"""

        def update_method():
            cls._update_broker_portfolio(broker_name)

        return update_method

    @classmethod
    def _update_broker_portfolio(cls, broker_name: BrokerName):
        """Generic method to update any broker portfolio"""
        broker_config = cls.BROKER_CONFIGS.get(broker_name)
        if not broker_config:
            cls.logger.error(f"Unknown broker: {broker_name}")
            return

        cls.logger.info(f"Updating {broker_name.upper()} Portfolio")

        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            # Get broker configuration
            broker_factory = BrokerFactory()
            config = broker_factory.create_config(broker_name)

            if not config or not config.is_enabled():
                cls.logger.warning(f"{broker_name.capitalize()} is not enabled, skipping update")
                return

            # Create update service with the proper config
            update_service_class = broker_config["update_service_class"]
            update_service = update_service_class(config=config)

            # Attempt to connect the broker service if not already connected
            service_attr = broker_config["service_attr"]
            broker_service = getattr(update_service, service_attr)
            connection_check = broker_config["connection_check"]
            connection_method = broker_config["connection_method"]

            # Check if service is connected
            is_connected = False
            if connection_check == "is_connected":
                is_connected = broker_service.is_connected()
            elif connection_check == "get_client":
                is_connected = broker_service.get_client() is not None

            if not is_connected:
                cls.logger.info(f"{broker_name.capitalize()} service not connected, attempting to connect...")
                try:
                    if connection_method:
                        # For services that need explicit connection (like DeGiro)
                        getattr(broker_service, connection_method)()
                        cls.logger.info(f"{broker_name.capitalize()} service connected successfully")
                    else:
                        # For services that connect during initialization (like IBKR, Bitvavo)
                        cls.logger.info(f"{broker_name.capitalize()} service connection handled during initialization")
                except Exception as connect_error:
                    cls.logger.warning(f"Failed to connect {broker_name.capitalize()} service: {connect_error}")
                    cls.logger.info(cls.PROCEED_WITH_CACHED_DATA_MSG)

            # Perform the update
            update_service.update_all()

        except CredentialsException as error:
            cls.logger.error(f"{error}", exc_info=DEBUG_MODE)
        except Exception as error:
            cls.logger.error(f"Update {broker_name.upper()} failed with {error}", exc_info=DEBUG_MODE)

    @staticmethod
    def start():
        if JobsScheduler.scheduler:
            JobsScheduler.logger.warning("JobsScheduler already started")
            return

        JobsScheduler.logger.info("Starting JobsScheduler")
        JobsScheduler.scheduler = BackgroundScheduler()

        JobsScheduler.scheduler.start()

        # This job runs once at startup to configure all other jobs based on broker settings
        # The Broker Settings may be read from the database, so we defer this to ensure DB is ready
        JobsScheduler.scheduler.add_job(
            JobsScheduler._configure_jobs,
            id="configure_jobs",
            trigger="date",
            run_date=timezone.now(),
            max_instances=1,
            replace_existing=True,
        )

    @staticmethod
    def _with_broker_config(broker_factory, broker, action):
        try:
            config = broker_factory.create_config(broker["name"])
            if (
                config
                and config.is_enabled()
                and (not broker["check_offline"] or not getattr(config, "offline_mode", False))
            ):
                action(config, broker)
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to process {broker['name'].capitalize()}: {e}")

    @staticmethod
    def _configure_jobs():
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to initialize BrokerFactory: {e}")
            return

        for broker in JobsScheduler.get_brokers():
            JobsScheduler._with_broker_config(
                broker_factory,
                broker,
                lambda config, b: JobsScheduler.scheduler.add_job(
                    b["update_method"],
                    id=b["job_id"],
                    trigger=IntervalTrigger(minutes=config.update_frequency_minutes),
                    max_instances=1,
                    replace_existing=True,
                    next_run_time=timezone.now(),
                ),
            )

    @staticmethod
    def scheduler_info():
        JobsScheduler.logger.info("Scheduler Info:")
        for job in JobsScheduler.scheduler.get_jobs():
            JobsScheduler.logger.info(f"    Job: {job.name}: next run at {job.next_run_time}")

    @staticmethod
    def stop():
        if JobsScheduler.scheduler:
            JobsScheduler.scheduler.shutdown()
            JobsScheduler.logger.info("JobScheduler stopped")

    @staticmethod
    def update_portfolio():
        JobsScheduler.logger.info("Updating Portfolio")
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to initialize BrokerFactory: {e}")
            return

        for broker in JobsScheduler.get_brokers():
            JobsScheduler._with_broker_config(broker_factory, broker, lambda config, b: b["update_method"]())
