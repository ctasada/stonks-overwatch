from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from stonks_overwatch.core.exceptions import CredentialsException
from stonks_overwatch.services.brokers.bitvavo.services.update_service import UpdateService as BitvavoUpdateService
from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService as DegiroUpdateService
from stonks_overwatch.services.brokers.ibkr.services.update_service import UpdateService as IbkrUpdateService
from stonks_overwatch.settings import DEBUG_MODE
from stonks_overwatch.utils.core.logger import StonksLogger


class JobsScheduler:
    logger = StonksLogger.get_logger("stonks_overwatch.jobs_scheduler", "[JOB_SCHEDULER]")

    scheduler = None

    @classmethod
    def get_brokers(cls):
        """Get complete broker configurations with update methods"""
        return [
            {
                "name": "degiro",
                "job_id": "update_degiro_portfolio",
                "check_offline": True,
                "update_method": cls.update_degiro_portfolio,
            },
            {
                "name": "bitvavo",
                "job_id": "update_bitvavo_portfolio",
                "check_offline": True,
                "update_method": cls.update_bitvavo_portfolio,
            },
            {
                "name": "ibkr",
                "job_id": "update_ibkr_portfolio",
                "check_offline": False,
                "update_method": cls.update_ibkr_portfolio,
            },
        ]

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
            run_date=datetime.now(),
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
                    next_run_time=datetime.now(),
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

    @staticmethod
    def update_degiro_portfolio():
        JobsScheduler.logger.info("Updating DEGIRO Portfolio")
        try:
            degiro_update_service = DegiroUpdateService()
            degiro_update_service.update_all()
        except CredentialsException as error:
            JobsScheduler.logger.error(f"{error}", exc_info=DEBUG_MODE)
        except Exception as error:
            JobsScheduler.logger.error(f"Update DEGIRO failed with {error}", exc_info=DEBUG_MODE)

    @staticmethod
    def update_ibkr_portfolio():
        JobsScheduler.logger.info("Updating IBKR Portfolio")
        try:
            ibkr_update_service = IbkrUpdateService()
            ibkr_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update IBKR failed with {error}", exc_info=DEBUG_MODE)

    @staticmethod
    def update_bitvavo_portfolio():
        JobsScheduler.logger.info("Updating Bitvavo Portfolio")
        try:
            bitvavo_update_service = BitvavoUpdateService()
            bitvavo_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update Bitvavo failed with {error}", exc_info=DEBUG_MODE)
