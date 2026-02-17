import json

from django.urls import reverse

from stonks_overwatch.config.config import Config
from stonks_overwatch.context_processors import appearance_processor
from stonks_overwatch.views.settings import SettingsView

from django.test import RequestFactory, TestCase


class DarkModeVerificationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        Config.reset_global_for_tests()

    def test_appearance_processor(self):
        """Test that the appearance processor returns the correct theme."""
        # Set a specific appearance
        config = Config.get_global()
        config.appearance = "dark"

        request = self.factory.get("/")
        context = appearance_processor(request)

        self.assertEqual(context["APPEARANCE"], "dark")

    def test_settings_view_get_context(self):
        """Test that SettingsView GET returns appearance and currency in context."""
        config = Config.get_global()
        config.appearance = "light"
        config.base_currency = "USD"

        url = reverse("settings")
        request = self.factory.get(url)
        # Mocking Header to be AJAX to avoid standalone wrapper
        request.headers = {"X-Requested-With": "XMLHttpRequest"}

        view = SettingsView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        # Check context
        _context = response.context_data if hasattr(response, "context_data") else None
        # Since it's a TemplateResponse (from render), context is in context_data or similar
        # Actually render(request, ...) returns HttpResponse in Django 1.x-5.x,
        # but we can check the rendered content if needed, or use self.client.get

        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["APPEARANCE"], "light")
        self.assertEqual(response.context["BASE_CURRENCY"], "USD")

    def test_save_general_settings(self):
        """Test that POST to settings with broker_name='general' saves global settings."""
        url = reverse("settings")
        payload = {"broker_name": "general", "appearance": "dark", "base_currency": "GBP"}

        response = self.client.post(
            url, data=json.dumps(payload), content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify changes in config
        Config.reset_global_for_tests()  # Reload to ensure it's from DB
        config = Config.get_global()
        self.assertEqual(config.appearance, "dark")
        self.assertEqual(config.base_currency, "GBP")
