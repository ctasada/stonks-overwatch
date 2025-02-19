from django.http import HttpRequest

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

        return PortfolioId.ALL

    @staticmethod
    def set_selected_portfolio(request: HttpRequest, portfolio_id: PortfolioId):
        request.session[SessionManager.SESSION_SELECTED_PORTFOLIO] = portfolio_id.id

    @staticmethod
    def clear_selected_portfolio(request: HttpRequest):
        """Clear the selected portfolio from session."""
        if SessionManager.SESSION_SELECTED_PORTFOLIO in request.session:
            del request.session[SessionManager.SESSION_SELECTED_PORTFOLIO]
