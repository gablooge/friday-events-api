"""Environment-only smoke checks. No interview domain behaviour lives here."""

import django
import pytest
from django.conf import settings
from django.db import connection


def test_django_is_5x():
    assert django.VERSION[0] == 5


def test_expected_packages_installed():
    assert "rest_framework" in settings.INSTALLED_APPS
    assert "drf_spectacular" in settings.INSTALLED_APPS
    assert "core" in settings.INSTALLED_APPS
    import rest_framework_simplejwt  # noqa: F401  (installed, not configured)


@pytest.mark.django_db
def test_database_connection():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
