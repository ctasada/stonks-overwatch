from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService as DegiroUpdateService
from stonks_overwatch.utils.logger import StonksLogger

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
        degiro_config = DegiroConfig.default()

        if degiro_config.is_enabled() and not degiro_config.offline_mode:
            JobsScheduler.scheduler.add_job(
                JobsScheduler.update_degiro_portfolio,
                id='update_degiro_portfolio',
                trigger=IntervalTrigger(minutes=degiro_config.update_frequency_minutes),
                max_instances=1,
                replace_existing=True,
                next_run_time=datetime.now()
            )

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

    @staticmethod
    def update_degiro_portfolio():
        JobsScheduler.logger.info("Updating DEGIRO Portfolio")
        try:
            degiro_update_service = DegiroUpdateService()
            degiro_update_service.update_all()
        except Exception as error:
            JobsScheduler.logger.error(f"Update DEGIRO failed with {error}")
