import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.services.degiro.update_service import UpdateService

jobs_scheduler_logger = logging.getLogger("stocks_portfolio.jobs_scheduler")

class JobsScheduler:

    scheduler = None

    @staticmethod
    def start():
        if JobsScheduler.scheduler:
            jobs_scheduler_logger.warning("JobsScheduler already started")
            return

        jobs_scheduler_logger.info("Starting JobsScheduler")
        JobsScheduler.scheduler = BackgroundScheduler()
        degiro_config = DegiroConfig.default()

        JobsScheduler.scheduler.add_job(
            JobsScheduler.update_portfolio,
            id='update_portfolio',
            trigger=IntervalTrigger(minutes=degiro_config.update_frequency_minutes),
            max_instances=1,
            replace_existing=True,
            next_run_time=datetime.now()
        )

        JobsScheduler.scheduler.start()

    @staticmethod
    def scheduler_info():
        for job in JobsScheduler.scheduler.get_jobs():
            jobs_scheduler_logger.info(f"{job.name}")

    @staticmethod
    def stop():
        if JobsScheduler.scheduler:
            JobsScheduler.scheduler.shutdown()
            jobs_scheduler_logger.info("JobScheduler stopped")

    @staticmethod
    def update_portfolio():
        jobs_scheduler_logger.info("Updating Portfolio")
        try:
            update_service = UpdateService()
            update_service.update_all()
        except Exception as error:
            jobs_scheduler_logger.error(f"Update failed with {error}")
