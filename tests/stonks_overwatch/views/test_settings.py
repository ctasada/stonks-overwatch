import json

from stonks_overwatch.views.settings import SettingsView

import pytest
from django.test import RequestFactory
from unittest.mock import MagicMock, patch


@pytest.mark.django_db
class TestSaveIntegrationSettings:
    def setup_method(self):
        self.factory = RequestFactory()
        self.view = SettingsView()

    def _post(self, payload):
        request = self.factory.post(
            "/settings",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        return self.view.post(request)

    @patch("stonks_overwatch.views.settings.cache")
    @patch("stonks_overwatch.views.settings.Config")
    def test_save_logodev_provider(self, mock_config_cls, mock_cache):
        mock_config = MagicMock()
        mock_config._settings_cache = {}
        mock_config_cls.get_global.return_value = mock_config

        response = self._post(
            {
                "action": "save_integration",
                "integration_name": "logo_provider",
                "provider": "logodev",
                "api_key": "pk_test",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        mock_config.save_setting.assert_called_once()
        assert mock_config.save_setting.call_args[0][0] == "integration_logo_provider"

    @patch("stonks_overwatch.views.settings.cache")
    @patch("stonks_overwatch.views.settings.Config")
    def test_save_logostream_provider(self, mock_config_cls, mock_cache):
        mock_config = MagicMock()
        mock_config._settings_cache = {}
        mock_config_cls.get_global.return_value = mock_config

        response = self._post(
            {
                "action": "save_integration",
                "integration_name": "logo_provider",
                "provider": "logostream",
                "api_key": "ls_key",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

    @patch("stonks_overwatch.views.settings.encrypt_integration_config")
    @patch("stonks_overwatch.views.settings.cache")
    @patch("stonks_overwatch.views.settings.Config")
    def test_save_none_provider_disables_integration(self, mock_config_cls, mock_cache, mock_encrypt):
        mock_config = MagicMock()
        mock_config._settings_cache = {}
        mock_config_cls.get_global.return_value = mock_config
        mock_encrypt.side_effect = lambda payload: payload

        response = self._post(
            {
                "action": "save_integration",
                "integration_name": "logo_provider",
                "provider": "none",
                "api_key": "",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        saved_payload = mock_config.save_setting.call_args[0][1]
        assert saved_payload["provider"] == "none"
        assert saved_payload["api_key"] == ""

    def test_missing_integration_name_returns_400(self):
        response = self._post(
            {
                "action": "save_integration",
                "provider": "logodev",
                "api_key": "pk_test",
            }
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_unknown_integration_name_returns_400(self):
        response = self._post(
            {
                "action": "save_integration",
                "integration_name": "nonexistent_integration",
                "api_key": "pk_test",
            }
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_invalid_logo_provider_returns_400(self):
        response = self._post(
            {
                "action": "save_integration",
                "integration_name": "logo_provider",
                "provider": "evil_provider",
                "api_key": "some_key",
            }
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data
