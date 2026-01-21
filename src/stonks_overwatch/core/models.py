from django.db import models

from stonks_overwatch.utils.core.logger import StonksLogger


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
