
from typing import Optional

from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import resolve

from stonks_overwatch.config.config import Config
from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.utils.logger import StonksLogger

class DeGiroAuthMiddleware:
    PUBLIC_URLS = {'login'}

    logger = StonksLogger.get_logger("stonks_overwatch.degiro_auth", "DEGIRO|AUTH_MIDDLEWARE")

    def __init__(self, get_response):
        self.get_response = get_response
        self.degiro_service = DeGiroService()

    def __call__(self, request):
        current_url = resolve(request.path_info).url_name

        if Config.default().is_degiro_enabled():
            if self._should_check_connection(request):
                try:
                    self._authenticate_user(request)
                except ConnectionError:
                    pass

            if not self._is_authenticated(request) and not self._is_public_url(current_url):
                self.logger.warning("User not authenticated, redirecting to Login page...")
                return redirect('login')

        return self.get_response(request)

    def _should_check_connection(self, request) -> bool:
        has_default_credentials = (DegiroConfig.default().credentials is not None
                and DegiroConfig.default().get_credentials.username is not None
                and DegiroConfig.default().get_credentials.password is not None)

        return has_default_credentials or 'session_id' in request.session

    def _is_public_url(self, url_name: Optional[str]) -> bool:
        return url_name in self.PUBLIC_URLS

    def _authenticate_user(self, request: HttpRequest) -> None:
        request.session['is_authenticated'] = self.degiro_service.check_connection()
        request.session['session_id'] = self.degiro_service.get_session_id()

    def _is_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if the user is authenticated by verifying:
        1. Session has is_authenticated flag
        2. Session has valid session_id
        """
        try:
            # Check if basic session authentication exists
            if not request.session.get('is_authenticated'):
                self.logger.debug("Session not authenticated")
                return False

            # Verify session_id exists
            session_id = request.session.get('session_id')
            if not session_id:
                self.logger.debug("No session ID found")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking authentication status: {str(e)}")
            return False
