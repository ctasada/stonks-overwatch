"""
Integration tests for database switching functionality.

This test verifies that the database switching works correctly in practice
by testing actual database operations with different DEMO_MODE settings.
"""

import os

from django.db import connections

from stonks_overwatch.services.brokers.models import BrokersConfiguration

from django.test import TestCase, override_settings
from unittest.mock import patch


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        },
        "demo": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        },
    },
    DATABASE_ROUTERS=["stonks_overwatch.utils.database.db_router.DatabaseRouter"],
)
class TestDatabaseIntegration(TestCase):
    """Integration tests for database switching."""

    # Allow access to both databases in tests
    databases = ["default", "demo"]

    def setUp(self):
        """Set up test databases."""
        # Ensure both databases have the required tables
        from django.core.management import call_command

        call_command("migrate", database="default", verbosity=0)
        call_command("migrate", database="demo", verbosity=0)

    def tearDown(self):
        """Clean up after each test."""
        # Clear cache to ensure tests don't interfere with each other
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        is_demo_mode.cache_clear()

    def test_production_mode_uses_default_database(self):
        """Test that production mode operations use the default database."""
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        is_demo_mode.cache_clear()

        with patch.dict(os.environ, {"DEMO_MODE": "False"}, clear=False):
            # Get initial counts
            initial_default_count = BrokersConfiguration.objects.using("default").count()
            initial_demo_count = BrokersConfiguration.objects.using("demo").count()

            # Create a test record
            config = BrokersConfiguration.objects.create(broker_name="test_broker_unique", enabled=True, credentials={})

            # Verify it was created in the default database
            self.assertEqual(config._state.db, "default")

            # Verify it was added to default but not demo
            final_default_count = BrokersConfiguration.objects.using("default").count()
            final_demo_count = BrokersConfiguration.objects.using("demo").count()

            self.assertEqual(final_default_count, initial_default_count + 1)
            self.assertEqual(final_demo_count, initial_demo_count)

    def test_demo_mode_uses_demo_database(self):
        """Test that demo mode operations use the demo database."""
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        is_demo_mode.cache_clear()

        with patch.dict(os.environ, {"DEMO_MODE": "True"}, clear=False):
            # Get initial counts
            initial_default_count = BrokersConfiguration.objects.using("default").count()
            initial_demo_count = BrokersConfiguration.objects.using("demo").count()

            # Create a test record
            config = BrokersConfiguration.objects.create(broker_name="demo_broker_unique", enabled=True, credentials={})

            # Verify it was created in the demo database
            self.assertEqual(config._state.db, "demo")

            # Verify it was added to demo but not default
            final_default_count = BrokersConfiguration.objects.using("default").count()
            final_demo_count = BrokersConfiguration.objects.using("demo").count()

            self.assertEqual(final_default_count, initial_default_count)
            self.assertEqual(final_demo_count, initial_demo_count + 1)

    def test_database_switching_isolation(self):
        """Test that switching between modes maintains data isolation."""
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        # Create record in production mode
        is_demo_mode.cache_clear()
        with patch.dict(os.environ, {"DEMO_MODE": "False"}, clear=False):
            BrokersConfiguration.objects.create(broker_name="production_broker_isolation", enabled=True, credentials={})

        # Create record in demo mode
        is_demo_mode.cache_clear()
        with patch.dict(os.environ, {"DEMO_MODE": "True"}, clear=False):
            BrokersConfiguration.objects.create(broker_name="demo_broker_isolation", enabled=True, credentials={})

        # Verify isolation - check that each record exists only in its intended database
        default_has_production = (
            BrokersConfiguration.objects.using("default").filter(broker_name="production_broker_isolation").exists()
        )
        default_has_demo = (
            BrokersConfiguration.objects.using("default").filter(broker_name="demo_broker_isolation").exists()
        )

        demo_has_production = (
            BrokersConfiguration.objects.using("demo").filter(broker_name="production_broker_isolation").exists()
        )
        demo_has_demo = BrokersConfiguration.objects.using("demo").filter(broker_name="demo_broker_isolation").exists()

        # Production record should only be in default database
        self.assertTrue(default_has_production)
        self.assertFalse(demo_has_production)

        # Demo record should only be in demo database
        self.assertTrue(demo_has_demo)
        self.assertFalse(default_has_demo)

    def test_database_connections_are_separate(self):
        """Test that the database connections are properly separated."""
        # Get connections to both databases
        default_conn = connections["default"]
        demo_conn = connections["demo"]

        # Verify they are different connections
        self.assertNotEqual(default_conn, demo_conn)

        # Verify they have different database names (both :memory: but different instances)
        self.assertNotEqual(id(default_conn), id(demo_conn))
