from datetime import timedelta

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from stonks_overwatch.middleware.license import LicenseMiddleware

import pytest
from django.test import RequestFactory, override_settings


class DummyLogger:
    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def info(msg):
        pass

    @staticmethod
    def error(msg):
        pass


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture(autouse=True)
def patch_logger(monkeypatch):
    monkeypatch.setattr("stonks_overwatch.middleware.license.LicenseMiddleware.logger", DummyLogger())


@pytest.fixture
def mock_build_info(monkeypatch):
    def _mock_build_info(days_ago):
        build_date = timezone.now() - timedelta(days=days_ago)
        build_info = {
            "trial_mode": True,
            "build_date": build_date.isoformat(),
            "expiration_days": 30,
        }

        def mock_load_build_info(self):
            self.build_info = build_info

        monkeypatch.setattr(LicenseMiddleware, "_load_build_info", mock_load_build_info)
        return build_info

    return _mock_build_info


@pytest.fixture
def get_response():
    def _get_response(request):
        return HttpResponse()

    return _get_response


@override_settings(TRIAL_MODE=True, LICENSE_EXPIRATION_DAYS=30)
def test_expiration_not_reached(rf, mock_build_info, get_response):
    # Simulate build date 10 days ago
    mock_build_info(10)
    middleware = LicenseMiddleware(get_response)
    middleware._calculate_expiration()
    assert middleware.days_remaining > 0
    req = rf.get("/")
    resp = middleware.process_request(req)
    assert resp is None  # Should allow access


@override_settings(TRIAL_MODE=True, LICENSE_EXPIRATION_DAYS=30)
def test_expiration_reached(rf, mock_build_info, get_response):
    # Simulate build date 40 days ago
    mock_build_info(40)
    middleware = LicenseMiddleware(get_response)
    middleware._calculate_expiration()

    # Test regular request - should redirect to expired page
    req = rf.get("/")
    resp = middleware.process_request(req)
    assert isinstance(resp, HttpResponseRedirect)
    assert resp.status_code == 302
    assert resp.url == "/expired"

    # Test exempt URLs - should allow access
    for exempt_url in ["/expired", "/static/test.css", "/media/test.jpg", "/favicon.ico"]:
        req = rf.get(exempt_url)
        resp = middleware.process_request(req)
        assert resp is None, f"Should allow access to exempt URL: {exempt_url}"

    # Test already on expired page - should allow access
    req = rf.get("/expired")
    resp = middleware.process_request(req)
    assert resp is None


@override_settings(TRIAL_MODE=False)
def test_middleware_disabled(rf, get_response):
    middleware = LicenseMiddleware(get_response)
    req = rf.get("/")
    resp = middleware.process_request(req)
    assert resp is None  # Should allow access
