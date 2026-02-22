from stonks_overwatch.config.config import Config
from stonks_overwatch.core.models import GlobalConfiguration
from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
from stonks_overwatch.integrations.logos.logodev import LogoDevIntegration
from stonks_overwatch.integrations.logos.registry import LogoIntegrationRegistry
from stonks_overwatch.integrations.logos.types import LogoType
from stonks_overwatch.services.brokers.encryption_utils import encrypt_integration_config
from stonks_overwatch.services.brokers.models import BrokersConfiguration

import pytest


class DummyResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.ok = status_code < 400

    def close(self) -> None:
        return None


def test_logodev_is_active() -> None:
    assert LogoDevIntegration(api_key="token", enabled=True).is_active()
    assert not LogoDevIntegration(api_key="", enabled=True).is_active()
    assert not LogoDevIntegration(api_key="token", enabled=False).is_active()


def test_logodev_get_logo_url_returns_empty_on_404(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=404)

    monkeypatch.setattr("stonks_overwatch.integrations.logos.logodev.requests.get", fake_get)

    integration = LogoDevIntegration(api_key="token", enabled=True)
    url = integration.get_logo_url(LogoType.STOCK, symbol="AAPL")
    assert url == ""


def test_logodev_get_logo_url_uses_isin(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=200)

    monkeypatch.setattr("stonks_overwatch.integrations.logos.logodev.requests.get", fake_get)

    integration = LogoDevIntegration(api_key="token", enabled=True)
    url = integration.get_logo_url(LogoType.STOCK, symbol="AAPL", isin="US0378331005")
    assert "isin/US0378331005" in url


def test_ibkr_get_logo_url_invalid_conid() -> None:
    integration = IbkrLogoIntegration(enabled=True)
    assert integration.get_logo_url(LogoType.STOCK, symbol="AAPL", conid="") == ""
    assert integration.get_logo_url(LogoType.STOCK, symbol="AAPL", conid="abc") == ""


def test_ibkr_get_logo_url_success(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=200)

    monkeypatch.setattr("stonks_overwatch.integrations.logos.ibkr.requests.get", fake_get)

    integration = IbkrLogoIntegration(enabled=True)
    url = integration.get_logo_url(LogoType.STOCK, symbol="AAPL", conid="30314149", theme="light")
    assert "conid=30314149" in url
    assert "type=mark_light" in url


@pytest.mark.django_db
def test_registry_builds_active_integrations() -> None:
    Config.reset_global_for_tests()
    encrypted = encrypt_integration_config({"enabled": True, "api_key": "token"})
    GlobalConfiguration.set_setting("integration_logodev", encrypted)

    BrokersConfiguration.objects.update_or_create(
        broker_name="ibkr",
        defaults={"enabled": True, "credentials": {}},
    )

    integrations = LogoIntegrationRegistry.get_active_integrations()
    assert len(integrations) == 2
    assert isinstance(integrations[0], LogoDevIntegration)
    assert isinstance(integrations[1], IbkrLogoIntegration)


@pytest.mark.django_db
def test_registry_skips_disabled_integrations() -> None:
    Config.reset_global_for_tests()
    encrypted = encrypt_integration_config({"enabled": False, "api_key": "token"})
    GlobalConfiguration.set_setting("integration_logodev", encrypted)

    BrokersConfiguration.objects.update_or_create(
        broker_name="ibkr",
        defaults={"enabled": False, "credentials": {}},
    )

    integrations = LogoIntegrationRegistry.get_active_integrations()
    assert integrations == []
