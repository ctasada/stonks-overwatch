import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from degiro.config.degiro_config import DegiroConfig
from degiro.services.update_service import UpdateService

jobs_scheduler_logger = logging.getLogger("stocks_portfolio.jobs_scheduler")

class JobsScheduler:

    initialised = False

    @staticmethod
    def start():
        if JobsScheduler.initialised:
            jobs_scheduler_logger.warning("JobsScheduler already started")
            return

        jobs_scheduler_logger.info("Starting JobsScheduler")
        scheduler = BackgroundScheduler()
        degiro_config = DegiroConfig.default()
        scheduler.add_job(
            JobsScheduler.update_portfolio,
            trigger='interval',
            minutes=degiro_config.update_frequency_minutes,
            next_run_time=datetime.now()
        )
        scheduler.start()

    @staticmethod
    def update_portfolio():
        jobs_scheduler_logger.info("Updating Portfolio")
        update_service = UpdateService()
        update_service.update_all()
