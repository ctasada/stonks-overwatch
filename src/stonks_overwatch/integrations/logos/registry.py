from stonks_overwatch.config.config import Config
from stonks_overwatch.constants.brokers import BrokerName
from stonks_overwatch.integrations.logos.base import LogoIntegration
from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
from stonks_overwatch.integrations.logos.logodev import LogoDevIntegration
from stonks_overwatch.integrations.logos.logostream import LogostreamIntegration
from stonks_overwatch.services.brokers.encryption_utils import decrypt_integration_config
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository
from stonks_overwatch.utils.core.logger import StonksLogger

_PROVIDER_CLASSES = {
    "logodev": LogoDevIntegration,
    "logostream": LogostreamIntegration,
}


class LogoIntegrationRegistry:
    logger = StonksLogger.get_logger("stonks_overwatch.integrations.logos", "[LOGO|REGISTRY]")

    @staticmethod
    def _build_logo_provider_integration() -> LogoIntegration | None:
        """Build the configured third-party logo provider integration (at most one)."""
        cfg = decrypt_integration_config(Config.get_global().get_setting("integration_logo_provider", {}))
        if not isinstance(cfg, dict):
            return None
        provider = cfg.get("provider", "").strip().lower()
        api_key = cfg.get("api_key", "").strip()
        cls = _PROVIDER_CLASSES.get(provider)
        if cls is None:
            return None
        if not api_key:
            LogoIntegrationRegistry.logger.warning(
                f"Logo provider '{provider}' is configured but no API key found; skipping integration."
            )
            return None
        return cls(api_key=api_key)

    @staticmethod
    def _build_ibkr_integration() -> LogoIntegration | None:
        ibkr_config = BrokersConfigurationRepository.get_broker_by_name(BrokerName.IBKR)
        if ibkr_config is None:
            return None
        return IbkrLogoIntegration(enabled=ibkr_config.enabled)

    @staticmethod
    def get_integrations() -> list[LogoIntegration]:
        integrations = [
            LogoIntegrationRegistry._build_logo_provider_integration(),
            LogoIntegrationRegistry._build_ibkr_integration(),
        ]
        return [i for i in integrations if i is not None]

    @staticmethod
    def get_active_integrations() -> list[LogoIntegration]:
        return [i for i in LogoIntegrationRegistry.get_integrations() if i.is_active()]
