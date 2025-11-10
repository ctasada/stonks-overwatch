import os
from datetime import datetime, timezone

from django.conf import settings


def license_processor(request):
    """Add trial expiration info to template context"""
    if not getattr(settings, "TRIAL_MODE", True):
        return {}

    # Read build information
    build_date = getattr(settings, "BUILD_DATE", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    expiration_days = getattr(settings, "LICENSE_EXPIRATION_DAYS", 30)
    expiration_date = getattr(settings, "EXPIRATION_DATE", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))

    # Parse the dates with timezone awareness
    now = datetime.now(timezone.utc)

    # Handle expiration_date
    if isinstance(expiration_date, str):
        expiration_dt = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    else:
        # It's already a datetime
        expiration_dt = expiration_date if expiration_date.tzinfo else expiration_date.replace(tzinfo=timezone.utc)

    days_remaining = (expiration_dt - now).days

    return {
        "build_date": build_date,
        "days_remaining": days_remaining,
        "expiration_date": expiration_date,
        "expiration_days": expiration_days,
    }


def app_mode_processor(request):
    """Add app mode context to detect if running in Toga WebView or as webapp"""
    is_desktop_app = os.environ.get("STONKS_OVERWATCH_APP") == "1"
    return {
        "is_desktop_app": is_desktop_app,
        "is_webapp": not is_desktop_app,
    }
