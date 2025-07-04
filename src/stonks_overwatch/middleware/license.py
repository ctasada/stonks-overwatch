from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from stonks_overwatch.utils.core.logger import StonksLogger


class LicenseMiddleware(MiddlewareMixin):
    """
    Middleware to handle testing version expiration.

    This middleware:
    - Checks if the testing version has expired
    - Shows warnings when expiration is approaching
    - Blocks access to the application when expired
    - Provides graceful degradation with clear messaging
    """

    logger = StonksLogger.get_logger("stonks_overwatch.license", "[LICENSE_MIDDLEWARE]")

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        self.expiration_date = None
        self.days_remaining = None
        self.build_info = {}
        self._load_build_info()
        self._calculate_expiration()

    def _load_build_info(self):
        """Load build information from settings"""
        build_date = getattr(settings, "BUILD_DATE", datetime.now())
        # If build_date is a string, try to parse it
        if isinstance(build_date, str):
            try:
                build_date = datetime.fromisoformat(build_date.replace("Z", "+00:00"))
            except ValueError:
                # If parsing fails, use current time
                build_date = datetime.now()

        self.build_info = {
            "trial_mode": getattr(settings, "TRIAL_MODE", True),
            "expiration_days": getattr(settings, "LICENSE_EXPIRATION_DAYS", 30),
            "build_date": build_date.isoformat(),
            "expiration_date": getattr(settings, "EXPIRATION_DATE", None),
        }
        self.logger.info("Loaded build info from Django settings")

    def _calculate_expiration(self):
        """Calculate expiration date and remaining days"""
        try:
            if "expiration_date" in self.build_info and self.build_info["expiration_date"]:
                # Use explicit expiration timestamp from CI/CD
                expiration_str = self.build_info["expiration_date"]
                # Handle both with and without 'Z' suffix
                if expiration_str.endswith("Z"):
                    expiration_str = expiration_str[:-1] + "+00:00"
                self.expiration_date = datetime.fromisoformat(expiration_str)
            else:
                # Calculate from build date and expiration days
                build_date = self.build_info.get("build_date")
                if build_date:
                    if isinstance(build_date, str):
                        build_date = datetime.fromisoformat(build_date.replace("Z", "+00:00"))
                else:
                    build_date = getattr(settings, "BUILD_DATE", datetime.now())

                expiration_days = self.build_info.get("expiration_days", 30)
                self.expiration_date = build_date + timedelta(days=expiration_days)

            # Calculate days remaining (handle timezone-aware datetimes)
            now = datetime.now()
            if self.expiration_date.tzinfo:
                now = now.replace(tzinfo=self.expiration_date.tzinfo)
            elif now.tzinfo:
                # If now has timezone but expiration doesn't, make expiration timezone-aware
                self.expiration_date = self.expiration_date.replace(tzinfo=now.tzinfo)

            self.days_remaining = (self.expiration_date - now).days

            self.logger.info(f"Testing expiration calculated: {self.days_remaining} days remaining")

        except Exception as e:
            self.logger.error(f"Error calculating expiration: {e}")
            # Safe fallback - assume not expired
            self.days_remaining = 1
            self.expiration_date = datetime.now() + timedelta(days=1)

    def process_request(self, request):
        """Process incoming request and check expiration"""
        # Skip expiration check for certain URLs
        exempt_urls = [
            "/expired",
            "/static/",
            "/media/",
            "/favicon.ico",
        ]

        # Check if the current path should be exempt
        if any(request.path.startswith(url) for url in exempt_urls):
            return None

        # Check if expired
        if self._is_expired():
            return self._handle_expired_request(request)

        # Add expiration warning if expiring soon
        if self._is_expiring_soon():
            self._add_expiration_warning(request)

        return None

    def _is_expired(self):
        """Check if the license has expired"""
        if not self.build_info.get("trial_mode", True):
            return False

        if self.days_remaining is None:
            return False

        return self.days_remaining < 0

    def _is_expiring_soon(self, warning_days=5):
        """Check if the license is expiring soon"""
        if not self.build_info.get("trial_mode", True):
            return False

        if self.days_remaining is None:
            return False

        return 0 <= self.days_remaining <= warning_days

    def _handle_expired_request(self, request):
        """Handle requests when the license has expired"""
        # Log the expiration event
        self.logger.warning(f"License expired on {self.expiration_date.isoformat()}. ")

        # For regular requests, redirect to expired page
        if request.path != "/expired":
            return HttpResponseRedirect("/expired")

        # If already on expired page, let it through
        return None

    def _add_expiration_warning(self, request):
        """Add expiration warning information to the request"""
        if not hasattr(request, "_expiration_warning_added"):
            request.expiration_warning = {
                "days_remaining": self.days_remaining,
                "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
                "version": self.build_info.get("version", "unknown"),
            }
            request._expiration_warning_added = True

            # Log the warning (only once per session to avoid spam)
            session_key = f"expiration_warning_logged_{self.build_info.get('build_id', 'unknown')}"
            if not request.session.get(session_key, False):
                self.logger.info(
                    f"Trial version expiring soon: {self.days_remaining} days remaining. "
                    f"Version: {self.build_info.get('version', 'unknown')}"
                )
                request.session[session_key] = True
