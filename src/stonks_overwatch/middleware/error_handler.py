import traceback

from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class CustomErrorHandlerMiddleware(MiddlewareMixin):
    """
    Middleware that forces the use of our custom 500 error template
    even when DEBUG=True.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)

    def process_exception(self, request, exception):
        """
        Intercept any unhandled exceptions and render our custom 500 template.
        """
        # Get build information
        support_url = getattr(settings, "STONKS_OVERWATCH_SUPPORT_URL", "#")

        # Get exception info
        exc_type = type(exception).__name__
        exc_message = str(exception)

        context = {
            "exception_message": exc_message,
            "exception_type": exc_type,
            "support_url": support_url,
            # Only include traceback in development
            "traceback": traceback.format_exc() if settings.DEBUG else None,
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            # Try to render the main 500 template
            response = render(request, "500.html", context, status=500)
            return response
        except Exception:
            # Fallback to a simple error response if template rendering fails
            fallback_html = f"""
                <html><head><title>Server Error</title></head><body>
                <h1>Server Error</h1>
                <p><strong>Error Type:</strong> {exc_type}</p>
                <p><strong>Error Message:</strong> {exc_message}</p>
                <p><strong>Timestamp:</strong> {context["timestamp"]}</p>
                <p><a href=\"{support_url}\">Contact Support</a></p>
                </body></html>
            """
            return HttpResponseServerError(fallback_html, content_type="text/html")
