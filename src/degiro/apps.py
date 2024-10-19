import logging
import os

from django.apps import AppConfig


class DegiroConfig(AppConfig):
    logger = logging.getLogger("stocks_portfolio.degiro_config")
    default_auto_field = "django.db.models.BigAutoField"
    name = "degiro"

    def ready(self):
        # Guarantee that the Jobs are initialized only once
        if os.environ.get('RUN_MAIN'):
            self.logger.info("Degiro ready - RUN MAIN")
            from degiro.jobs.jobs_scheduler import JobsScheduler

            # Update Portfolio when the service starts
            JobsScheduler.update_portfolio()

            # Schedule automatic tasks
            JobsScheduler.start()
