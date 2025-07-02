import json

from django.http import JsonResponse
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.logger import StonksLogger


class ConfigurationView(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "VIEW|CONFIGURATION")

    def get(self, request) -> JsonResponse:
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        data = {
            "selected_portfolio": selected_portfolio.to_dict(),
            "available_portfolios": self.__get_portfolios(),
        }
        return JsonResponse(data)

    @staticmethod
    def __get_portfolios() -> list[dict]:
        portfolios = []
        for value in PortfolioId:
            if value == PortfolioId.ALL:
                continue
            # Add only the enabled portfolios
            if Config.get_global().is_enabled(value):
                portfolios.append(value.to_dict())

        # If there are more than one portfolio, add the "All" option
        if len(portfolios) > 1:
            portfolios.insert(0, PortfolioId.ALL.to_dict())

        return portfolios

    def post(self, request) -> JsonResponse:
        try:
            data = json.loads(request.body)
            selected_portfolio = data.get("selected_portfolio")
            if selected_portfolio:
                SessionManager.set_selected_portfolio(request, PortfolioId.from_id(selected_portfolio))
        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON data with the UI Configuration", exc_info=True)

        return JsonResponse({}, status=204)
