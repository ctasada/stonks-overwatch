from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from stonks_overwatch.services.brokers.bitvavo.services.update_service import UpdateService as BitvavoUpdateService
from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService as DegiroUpdateService
from stonks_overwatch.services.brokers.ibkr.services.update_service import UpdateService as IbkrUpdateService
from stonks_overwatch.utils.core.logger import StonksLogger


class JobsScheduler:
    logger = StonksLogger.get_logger("stonks_overwatch.jobs_scheduler", "[JOB_SCHEDULER]")

    scheduler = None

    @staticmethod
    def start():
        if JobsScheduler.scheduler:
            JobsScheduler.logger.warning("JobsScheduler already started")
            return

        JobsScheduler.logger.info("Starting JobsScheduler")
        JobsScheduler.scheduler = BackgroundScheduler()

        # Get config using unified BrokerFactory
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            degiro_config = broker_factory.create_config("degiro")

            if degiro_config and degiro_config.is_enabled() and not degiro_config.offline_mode:
                JobsScheduler.scheduler.add_job(
                    JobsScheduler.update_degiro_portfolio,
                    id="update_degiro_portfolio",
                    trigger=IntervalTrigger(minutes=degiro_config.update_frequency_minutes),
                    max_instances=1,
                    replace_existing=True,
                    next_run_time=datetime.now(),
                )
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to get DEGIRO config: {e}")

        # Get IBKR config using unified BrokerFactory
        try:
            ibkr_config = broker_factory.create_config("ibkr")

            if ibkr_config and ibkr_config.is_enabled():
                JobsScheduler.scheduler.add_job(
                    JobsScheduler.update_ibkr_portfolio,
                    id="update_ibkr_portfolio",
                    trigger=IntervalTrigger(minutes=ibkr_config.update_frequency_minutes),
                    max_instances=1,
                    replace_existing=True,
                    next_run_time=datetime.now(),
                )
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to get IBKR config: {e}")

        # Get Bitvavo config using unified BrokerFactory
        try:
            bitvavo_config = broker_factory.create_config("bitvavo")

            if bitvavo_config and bitvavo_config.is_enabled() and not bitvavo_config.offline_mode:
                JobsScheduler.scheduler.add_job(
                    JobsScheduler.update_bitvavo_portfolio,
                    id="update_bitvavo_portfolio",
                    trigger=IntervalTrigger(minutes=bitvavo_config.update_frequency_minutes),
                    max_instances=1,
                    replace_existing=True,
                    next_run_time=datetime.now(),
                )
        except Exception as e:
            JobsScheduler.logger.error(f"Failed to get Bitvavo config: {e}")

        JobsScheduler.scheduler.start()

    @staticmethod
    def scheduler_info():
        for job in JobsScheduler.scheduler.get_jobs():
            JobsScheduler.logger.info(f"{job.name}")

    @staticmethod
    def stop():
        if JobsScheduler.scheduler:
            JobsScheduler.scheduler.shutdown()
            JobsScheduler.logger.info("JobScheduler stopped")

    @staticmethod
    def update_portfolio():
        JobsScheduler.logger.info("Updating Portfolio")
        JobsScheduler.update_degiro_portfolio()
        JobsScheduler.update_ibkr_portfolio()
        JobsScheduler.update_bitvavo_portfolio()

    @staticmethod
    def update_degiro_portfolio():
        JobsScheduler.logger.info("Updating DEGIRO Portfolio")
        try:
            degiro_update_service = DegiroUpdateService()
            degiro_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update DEGIRO failed with {error}")

    @staticmethod
    def update_ibkr_portfolio():
        JobsScheduler.logger.info("Updating IBKR Portfolio")
        try:
            ibkr_update_service = IbkrUpdateService()
            ibkr_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update IBKR failed with {error}")

    @staticmethod
    def update_bitvavo_portfolio():
        JobsScheduler.logger.info("Updating Bitvavo Portfolio")
        try:
            bitvavo_update_service = BitvavoUpdateService()
            bitvavo_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update Bitvavo failed with {error}")
