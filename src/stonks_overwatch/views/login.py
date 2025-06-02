
from degiro_connector.core.exceptions import DeGiroConnectionError, MaintenanceError
from degiro_connector.trading.models.credentials import Credentials
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.config.degiro_credentials import DegiroCredentials
from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler
from stonks_overwatch.services.degiro.degiro_service import CredentialsManager, DeGiroService
from stonks_overwatch.utils.logger import StonksLogger

class Login(View):
    """
    View for the login page.
    Handles user authentication and connection to DeGiro.

    The view has 3 states:
    * Initial state: The user is prompted to enter their username and password.
    * TOTP required: The user is prompted to enter their 2FA code.
    * Loading: The user is shown a loading indicator while the portfolio is updated.
    """
    logger = StonksLogger.get_logger("stonks_overwatch.login", "VIEW|LOGIN")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = None

    def get(self, request):
        show_otp = False
        show_loading = False

        if request.session.get('is_authenticated'):
            self.logger.info("User is already authenticated. Redirecting to dashboard.")
            show_loading = True

        context = {
            "show_otp": show_otp,
            "show_loading": show_loading
        }
        return render(request, "login.html", context=context, status=200)

    def post(self, request):
        update_portfolio = request.POST.get('update_portfolio') or False
        if update_portfolio:
            # Update portfolio data before loading the dashboard
            JobsScheduler.update_portfolio()

            return redirect('dashboard')

        credentials = DegiroCredentials.from_request(request)
        username = request.POST.get('username') or credentials.username
        password = request.POST.get('password') or credentials.password
        one_time_password = request.POST.get('2fa_code') or credentials.one_time_password
        show_otp = False
        show_loading = False

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "login.html", context={"show_otp": show_otp}, status=400)

        try:
            self._authenticate_and_connect(request, username, password, one_time_password)
        except MaintenanceError:
            messages.warning(request, "DeGiro is currently under maintenance. Please try again later.")
        except DeGiroConnectionError as degiro_error:
            show_otp = self._handle_degiro_error(request, degiro_error, username, password)
        except ConnectionError as connection_error:
            self.logger.error(f"Connection error: {connection_error}")
            messages.error(request, "A connection error occurred. Please try again.")
        except Exception as e:
            self.logger.exception(f"Unexpected error during login: {e}")
            messages.error(request, "An unexpected error occurred. Please contact support.")

        if request.session.get('is_authenticated'):
            request.session['session_id'] = self.degiro_service.get_session_id()
            show_loading = True

        context = {
            "show_otp": show_otp,
            "show_loading": show_loading
        }

        return render(request, "login.html", context=context, status=200)

    def _authenticate_and_connect(self, request, username, password, one_time_password):
        self._store_credentials_in_session(request, username, password)
        credentials = Credentials(username=username, password=password, one_time_password=one_time_password)
        if not self.degiro_service:
            self.degiro_service = DeGiroService()
        self.degiro_service.set_credentials(CredentialsManager(credentials))

        self.logger.info("Attempting to connect to DeGiro...")
        self.degiro_service.connect()
        request.session['is_authenticated'] = True
        self.logger.info("Login successful.")

    def _handle_degiro_error(self, request, error, username, password):
        if error.error_details.status_text == 'totpNeeded':
            self._store_credentials_in_session(request, username, password)
            self.logger.info("TOTP required. Prompting user for 2FA code.")
            return True
        else:
            self.logger.error(f"DeGiro connection error: {error.error_details.status_text}")
            messages.error(request, error.error_details.status_text)
            return False

    def _store_credentials_in_session(self, request, username, password):
        """Helper function to store credentials in the session"""
        credentials = DegiroCredentials(
            username=username,
            password=password
        )
        request.session['credentials'] = credentials.to_dict()
        request.session.modified = True
        request.session.save()
