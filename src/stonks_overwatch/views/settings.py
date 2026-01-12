import json

import pyotp
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.theme import get_theme_colors


class SettingsView(View):
    """
    View for handling broker settings in a Bootstrap modal.

    GET: Returns the settings modal content (HTML fragment for AJAX requests)
    POST: Saves broker configuration changes
    """

    logger = StonksLogger.get_logger("stonks_overwatch.views.settings", "[VIEW|SETTINGS]")

    def __init__(self, **kwargs):
        """Initialize the view with repository instance."""
        super().__init__(**kwargs)
        self.repository = BrokersConfigurationRepository()

    def get(self, request) -> HttpResponse:
        """
        Handle GET request for settings page.

        Args:
            request: Django HTTP request object

        Returns:
            HttpResponse: Rendered HTML response from settings_content.html
                - HTML fragment for AJAX requests (modal in base.html)
                - Full HTML page for regular requests (native app WebView)
        """
        is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # Load broker configurations
        degiro_config = self.repository.get_broker_by_name("degiro")
        bitvavo_config = self.repository.get_broker_by_name("bitvavo")
        ibkr_config = self.repository.get_broker_by_name("ibkr")

        # Handle dark mode (for native app WebView)
        dark_mode_param = request.GET.get("dark_mode", "0")
        is_dark_mode = dark_mode_param.lower() in ["1", "true"]
        theme_colors = get_theme_colors(is_dark_mode)

        # Prepare context data
        context = {
            "degiro_config": degiro_config,
            "bitvavo_config": bitvavo_config,
            "ibkr_config": ibkr_config,
            "is_dark_mode": is_dark_mode,
            "is_standalone": not is_ajax_request,  # Wrap in HTML structure for non-AJAX requests
            # Pass all theme colors from theme.py
            **theme_colors,
        }

        # Always return the content component (it handles standalone vs fragment internally)
        return render(request, "components/settings_content.html", context)

    def post(self, request) -> JsonResponse:
        """
        Handle POST request to save broker configuration or generate TOTP code.

        Args:
            request: Django HTTP request object containing JSON payload

        Expected JSON payload for saving configuration:
        {
            "broker_name": "degiro" | "bitvavo" | "ibkr",
            "enabled": true | false,
            "credentials": {
                "username": "...",
                "password": "...",
                "totp_secret_key": "...",
                // OR for bitvavo:
                "apikey": "...",
                "apisecret": "..."
            },
            "update_frequency": 5
        }

        Expected JSON payload for TOTP code generation:
        {
            "action": "generate_totp",
            "secret": "TOTP_SECRET_KEY"
        }

        Returns:
            JsonResponse: Success or error response
        """
        try:
            data = json.loads(request.body)

            # Handle TOTP code generation request
            if data.get("action") == "generate_totp":
                return self._generate_totp_code(data)

            # Handle broker configuration save
            broker_name = data.get("broker_name")

            if not broker_name:
                self.logger.error("broker_name is missing from request data")
                return JsonResponse({"error": "broker_name is required"}, status=400)

            broker_config = self.repository.get_broker_by_name(broker_name)

            if not broker_config:
                self.logger.error(f"Broker '{broker_name}' not found in database")
                return JsonResponse({"error": f"Broker '{broker_name}' not found"}, status=404)

            # Update credentials if provided
            if "credentials" in data:
                self.repository.update_broker_credentials(broker_config, data["credentials"])

            # Update enabled if provided
            if "enabled" in data:
                broker_config.enabled = data["enabled"]

            # Update update_frequency if provided
            if "update_frequency" in data:
                broker_config.update_frequency = data["update_frequency"]

            # Save configuration
            self.repository.save_broker_configuration(broker_config)
            self.logger.info(f"Configuration saved successfully for broker: {broker_name}")

            return JsonResponse({"success": True, "message": "Configuration saved successfully"})

        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON data in settings POST request", exc_info=True)
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            self.logger.error(f"Failed to process request: {e}", exc_info=True)
            return JsonResponse({"error": "Failed to process request. Please try again later."}, status=500)

    def _generate_totp_code(self, data: dict) -> JsonResponse:
        """
        Generate TOTP verification code for a given secret.

        Args:
            data: Request data dictionary containing 'secret' key

        Returns:
            JsonResponse: TOTP code or error
        """
        try:
            secret = data.get("secret", "").strip()
            if not secret:
                return JsonResponse({"error": "Secret is required"}, status=400)

            totp = pyotp.TOTP(secret)
            code = totp.now()

            return JsonResponse({"code": code})

        except Exception as e:
            self.logger.error(f"Failed to generate TOTP code: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid TOTP secret"}, status=400)
