from datetime import datetime, timezone

from django.conf import settings
from django.shortcuts import render
from django.views import View


class ExpiredView(View):
    def get(self, request):
        """View shown when the license has expired"""
        build_date = getattr(settings, "BUILD_DATE", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        expiration_date = getattr(settings, "EXPIRATION_DATE", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        expiration_days = getattr(settings, "LICENSE_EXPIRATION_DAYS", 30)
        version = getattr(settings, "VERSION", "Unknown")
        support_url = settings.STONKS_OVERWATCH_SUPPORT_URL

        # Convert dates to timezone-aware datetimes
        if isinstance(build_date, str):
            build_date = datetime.strptime(build_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        elif isinstance(build_date, datetime) and build_date.tzinfo is None:
            build_date = build_date.replace(tzinfo=timezone.utc)

        if isinstance(expiration_date, str):
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        elif isinstance(expiration_date, datetime) and expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)

        # Calculate days until expiration
        now = datetime.now(timezone.utc)
        days_remaining = (expiration_date - now).days

        context = {
            "build_date": build_date,
            "expiration_date": expiration_date,
            "expiration_days": expiration_days,
            "version": version,
            "support_url": support_url,
            "days_remaining": days_remaining,
        }

        return render(request, "expired.html", context)
