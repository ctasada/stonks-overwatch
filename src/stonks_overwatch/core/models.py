from django.db import models
from django.utils import timezone

from stonks_overwatch.utils.core.logger import StonksLogger


class BrokerSyncLog(models.Model):
    """
    Tracks the last time each broker's data was successfully refreshed from the external API.

    This provides accurate "last refreshed" timestamps independent of when the most
    recent transaction or business event occurred.
    """

    class Meta:
        db_table = "broker_sync_log"
        verbose_name = "Broker Sync Log"
        verbose_name_plural = "Broker Sync Logs"
        get_latest_by = "synced_at"

    broker_name = models.CharField(max_length=50, db_index=True)
    synced_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)

    def __str__(self) -> str:
        status = "success" if self.success else "failed"
        return f"{self.broker_name}: {self.synced_at} ({status})"


class GlobalConfiguration(models.Model):
    """
    Model for storing global application configuration settings.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.core.models", "[GLOBAL_CONFIGURATION|MODEL]")

    class Meta:
        db_table = '"global_configuration"'
        verbose_name = "Global Configuration"
        verbose_name_plural = "Global Configurations"

    key = models.CharField(max_length=64, unique=True, help_text="Setting identifier")
    value = models.JSONField(help_text="Setting value (stored as JSON)")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_setting(cls, key: str, default: any = None) -> any:
        """
        Get a setting value from the database.
        """
        try:
            config = cls.objects.get(key=key)
            return config.value
        except cls.DoesNotExist:
            return default
        except Exception as e:
            cls.logger.error(f"Error getting setting '{key}': {e}")
            return default

    @classmethod
    def set_setting(cls, key: str, value: any) -> None:
        """
        Save a setting value to the database.
        """
        try:
            config, created = cls.objects.update_or_create(key=key, defaults={"value": value})
            cls.logger.debug(f"{'Created' if created else 'Updated'} setting '{key}' to {value}")
        except Exception as e:
            cls.logger.error(f"Error setting '{key}': {e}")
            raise
