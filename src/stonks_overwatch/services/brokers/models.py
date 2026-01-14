from asgiref.sync import sync_to_async
from django.db import models

from stonks_overwatch.utils.core.logger import StonksLogger

from .encryption_utils import decrypt_dict, encrypt_dict
from ...constants import BrokerName


class BrokersConfiguration(models.Model):
    logger = StonksLogger.get_logger("stonks_overwatch.brokers.models", "[BROKER_CONFIGURATION|MODEL]")

    class Meta:
        db_table = '"brokers_configuration"'

    broker_name = models.CharField(max_length=64, unique=True)
    enabled = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    update_frequency = models.IntegerField(help_text="Update frequency in minutes", default=5)
    credentials = models.JSONField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.credentials:
            try:
                self.credentials = decrypt_dict(self.credentials)
            except Exception as e:
                self.logger.error(f"Failed to decrypt credentials for broker '{self.broker_name}': {e}")

    def save(self, *args, **kwargs):
        if self.credentials:
            try:
                self.credentials = encrypt_dict(self.credentials)
            except Exception as e:
                self.logger.error(f"Failed to encrypt credentials for broker '{self.broker_name}': {e}")
        super().save(*args, **kwargs)
        # After saving, decrypt again for in-memory usage
        if self.credentials:
            try:
                self.credentials = decrypt_dict(self.credentials)
            except Exception as e:
                self.logger.error(f"Failed to decrypt credentials after save for broker '{self.broker_name}': {e}")


class BrokersConfigurationRepository:
    """
    Repository for managing BrokersConfiguration model instances.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.brokers.models", "[BROKER_CONFIGURATION|REPOSITORY]")

    @staticmethod
    @sync_to_async
    def get_all_brokers() -> list[BrokersConfiguration]:
        return list(BrokersConfiguration.objects.all())

    @staticmethod
    @sync_to_async
    def get_broker_by_name_async(broker_name: BrokerName) -> BrokersConfiguration | None:
        return BrokersConfigurationRepository.get_broker_by_name(broker_name)

    @staticmethod
    def get_broker_by_name(broker_name: BrokerName) -> BrokersConfiguration | None:
        try:
            return BrokersConfiguration.objects.get(broker_name=broker_name)
        except BrokersConfiguration.DoesNotExist:
            BrokersConfigurationRepository.logger.warning(
                f"BrokersConfiguration with name '{broker_name}' does not exist."
            )
            return None

    @staticmethod
    @sync_to_async
    def save_broker_configuration_async(broker_config: BrokersConfiguration) -> None:
        return BrokersConfigurationRepository.save_broker_configuration(broker_config)

    @staticmethod
    def save_broker_configuration(broker_config: BrokersConfiguration) -> None:
        broker_config.save()

    @staticmethod
    def update_broker_credentials(broker_config: BrokersConfiguration, credentials: dict) -> None:
        """
        Update credentials for a broker configuration.

        Ensures credentials is properly initialized as an empty dict if None,
        then updates it with the provided credentials.

        Args:
            broker_config: The broker configuration instance to update
            credentials: Dictionary of credentials to update
        """
        # Ensure credentials is initialized as an empty dict if None
        if broker_config.credentials is None:
            broker_config.credentials = {}
        # Update with new credentials
        broker_config.credentials.update(credentials)
