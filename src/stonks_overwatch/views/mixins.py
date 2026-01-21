from django.shortcuts import redirect

from stonks_overwatch.config.config import Config
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.utilities.session_manager import SessionManager


class CapabilityRequiredMixin:
    """
    Mixin for views that require a specific broker capability.
    If the selected portfolio does not support the capability,
    the user is redirected to the dashboard view.
    """

    required_capability: ServiceType = None

    def dispatch(self, request, *args, **kwargs):
        if self.required_capability:
            selected_portfolio = SessionManager.get_selected_portfolio(request)
            # Use specific portfolio ID if it's not ALL
            capabilities = Config.get_global().get_capabilities(selected_portfolio)

            if self.required_capability not in capabilities:
                return redirect("dashboard")

        return super().dispatch(request, *args, **kwargs)
