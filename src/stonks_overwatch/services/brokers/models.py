from asgiref.sync import sync_to_async
from django.db import models


class BrokersConfiguration(models.Model):
    class Meta:
        db_table = '"brokers_configuration"'

    broker_name = models.CharField(max_length=64, unique=True)
    enabled = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    update_frequency = models.IntegerField(help_text="Update frequency in minutes", default=5)
    credentials = models.JSONField()


class BrokersConfigurationRepository:
    """
    Repository for managing BrokersConfiguration model instances.
    """

    @staticmethod
    @sync_to_async
    def get_all_brokers() -> list[BrokersConfiguration]:
        return list(BrokersConfiguration.objects.all())

    @staticmethod
    @sync_to_async
    def get_broker_by_name(broker_name) -> BrokersConfiguration | None:
        try:
            return BrokersConfiguration.objects.get(broker_name=broker_name)
        except BrokersConfiguration.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async
    def save_broker_configuration(broker_config: BrokersConfiguration) -> None:
        # FIXME: Encrypt the credentials before saving it to the database.
        broker_config.save()
