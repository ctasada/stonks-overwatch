from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.constants.brokers import BrokerName
from stonks_overwatch.integrations.logos.base import LogoIntegration
from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
from stonks_overwatch.integrations.logos.logodev import LogoDevIntegration
from stonks_overwatch.services.brokers.encryption_utils import decrypt_integration_config
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository
from stonks_overwatch.utils.core.logger import StonksLogger


class LogoIntegrationRegistry:
    logger = StonksLogger.get_logger("stonks_overwatch.integrations.logos", "[LOGO|REGISTRY]")

    @staticmethod
    def _build_logodev_integration() -> LogoIntegration | None:
        cfg = decrypt_integration_config(Config.get_global().get_setting("integration_logodev", {}))
        if not isinstance(cfg, dict):
            return None
        api_key = cfg.get("api_key", "").strip()
        enabled = bool(cfg.get("enabled", False))
        if enabled and not api_key:
            LogoIntegrationRegistry.logger.warning(
                "Logo.dev is enabled but the API key could not be decrypted; skipping integration."
            )
        if not api_key:
            return None
        return LogoDevIntegration(api_key=api_key, enabled=enabled)

    @staticmethod
    def _build_ibkr_integration() -> LogoIntegration | None:
        ibkr_config = BrokersConfigurationRepository.get_broker_by_name(BrokerName.IBKR)
        if ibkr_config is None:
            return None
        return IbkrLogoIntegration(enabled=ibkr_config.enabled)

    @staticmethod
    def get_integrations() -> List[LogoIntegration]:
        integrations = [
            LogoIntegrationRegistry._build_logodev_integration(),
            LogoIntegrationRegistry._build_ibkr_integration(),
        ]
        return [i for i in integrations if i is not None]

    @staticmethod
    def get_active_integrations() -> List[LogoIntegration]:
        return [i for i in LogoIntegrationRegistry.get_integrations() if i.is_active()]
