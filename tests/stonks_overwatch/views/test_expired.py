from datetime import datetime, timedelta, timezone

from stonks_overwatch.views.expired import ExpiredView

import pytest
from django.test import RequestFactory, override_settings


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def expired_view():
    return ExpiredView()


@pytest.fixture
def mock_settings(settings):
    now = datetime.now(timezone.utc)
    settings.BUILD_DATE = now - timedelta(days=40)
    settings.EXPIRATION_DATE = now - timedelta(days=10)
    settings.LICENSE_EXPIRATION_DAYS = 30
    settings.VERSION = "1.0.0"
    settings.STONKS_OVERWATCH_SUPPORT_URL = "https://support.example.com"
    return settings


def test_expired_view_get(rf, expired_view, mock_settings):
    request = rf.get("/expired")
    response = expired_view.get(request)

    assert response.status_code == 200
    assert "Trial Version Expired" in response.content.decode()
    assert mock_settings.VERSION in response.content.decode()
    assert mock_settings.STONKS_OVERWATCH_SUPPORT_URL in response.content.decode()
    assert str(mock_settings.LICENSE_EXPIRATION_DAYS) in response.content.decode()


@override_settings(
    BUILD_DATE=datetime.now(timezone.utc) - timedelta(days=5),
    EXPIRATION_DATE=datetime.now(timezone.utc) + timedelta(days=25),
    LICENSE_EXPIRATION_DAYS=30,
    VERSION="1.0.0",
    STONKS_OVERWATCH_SUPPORT_URL="https://support.example.com",
)
def test_expired_view_not_expired(rf, expired_view):
    request = rf.get("/expired")
    response = expired_view.get(request)

    assert response.status_code == 200
    assert "Trial Version Info" in response.content.decode()


@override_settings(
    BUILD_DATE=datetime.now(timezone.utc) - timedelta(days=25),
    EXPIRATION_DATE=datetime.now(timezone.utc) + timedelta(days=5),
    LICENSE_EXPIRATION_DAYS=30,
    VERSION="1.0.0",
    STONKS_OVERWATCH_SUPPORT_URL="https://support.example.com",
)
def test_expired_view_expiring_soon(rf, expired_view):
    request = rf.get("/expired")
    response = expired_view.get(request)

    assert response.status_code == 200
    assert "Trial Version Expires Soon" in response.content.decode()
