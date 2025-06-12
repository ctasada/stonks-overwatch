from django.http import HttpRequest

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.models import PortfolioId

class SessionManager:
    # Session keys
    SESSION_SELECTED_PORTFOLIO = "selected_portfolio"

    @staticmethod
    def get_selected_portfolio(request: HttpRequest) -> PortfolioId:
        """Get the selected portfolio from session. Otherwise, return PortfolioId.ALL."""
        if SessionManager.SESSION_SELECTED_PORTFOLIO in request.session:
            portfolio_id = request.session.get(SessionManager.SESSION_SELECTED_PORTFOLIO)
            return PortfolioId.from_id(portfolio_id)

        available_portfolios = SessionManager.__get_available_portfolios()
        if len(available_portfolios) == 1:
            return available_portfolios[0]

        return PortfolioId.ALL

    @staticmethod
    def __get_available_portfolios() -> list[PortfolioId]:
        portfolios = []
        for value in PortfolioId:
            # Add only the enabled portfolios
            if Config().default().is_enabled(value):
                portfolios.append(value)
        return portfolios


    @staticmethod
    def set_selected_portfolio(request: HttpRequest, portfolio_id: PortfolioId):
        request.session[SessionManager.SESSION_SELECTED_PORTFOLIO] = portfolio_id.id

    @staticmethod
    def clear_selected_portfolio(request: HttpRequest):
        """Clear the selected portfolio from session."""
        if SessionManager.SESSION_SELECTED_PORTFOLIO in request.session:
            del request.session[SessionManager.SESSION_SELECTED_PORTFOLIO]
