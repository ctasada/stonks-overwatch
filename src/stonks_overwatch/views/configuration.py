import json

from django.http import JsonResponse
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.logger import StonksLogger


class ConfigurationView(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|CONFIGURATION]")

    def get(self, request) -> JsonResponse:
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        capabilities = Config.get_global().get_capabilities(selected_portfolio)

        portfolio_dict = selected_portfolio.to_dict()
        portfolio_dict["capabilities"] = [c.value for c in capabilities]

        data = {
            "selected_portfolio": portfolio_dict,
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
                portfolio_dict = value.to_dict()
                capabilities = Config.get_global().get_capabilities(value)
                portfolio_dict["capabilities"] = [c.value for c in capabilities]
                portfolios.append(portfolio_dict)

        # If there are more than one portfolio, add the "All" option
        if len(portfolios) > 1:
            all_portfolio_dict = PortfolioId.ALL.to_dict()
            all_capabilities = Config.get_global().get_capabilities(PortfolioId.ALL)
            all_portfolio_dict["capabilities"] = [c.value for c in all_capabilities]
            portfolios.insert(0, all_portfolio_dict)

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
