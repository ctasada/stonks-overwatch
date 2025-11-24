"""
Tests for the database router functionality.

This test verifies that the DatabaseRouter correctly routes database operations
based on the DEMO_MODE environment variable.
"""

import os

from stonks_overwatch.utils.database.db_router import DatabaseRouter

from django.test import TestCase
from unittest.mock import patch


class TestDatabaseRouter(TestCase):
    """Test cases for the DatabaseRouter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.router = DatabaseRouter()

    def test_production_mode_routing(self):
        """Test that production mode routes to default database."""
        with patch.dict(os.environ, {"DEMO_MODE": "False"}, clear=False):
            # Test read routing
            db_alias = self.router.db_for_read(None)
            self.assertEqual(db_alias, "default")

            # Test write routing
            db_alias = self.router.db_for_write(None)
            self.assertEqual(db_alias, "default")

    def test_demo_mode_routing(self):
        """Test that demo mode routes to demo database."""
        with patch.dict(os.environ, {"DEMO_MODE": "True"}, clear=False):
            # Test read routing
            db_alias = self.router.db_for_read(None)
            self.assertEqual(db_alias, "demo")

            # Test write routing
            db_alias = self.router.db_for_write(None)
            self.assertEqual(db_alias, "demo")

    def test_demo_mode_various_true_values(self):
        """Test that various true values for DEMO_MODE work correctly."""
        true_values = ["true", "True", "1"]

        for value in true_values:
            with patch.dict(os.environ, {"DEMO_MODE": value}, clear=False):
                db_alias = self.router.db_for_read(None)
                self.assertEqual(db_alias, "demo", f"Failed for DEMO_MODE={value}")

    def test_demo_mode_unset(self):
        """Test behavior when DEMO_MODE is not set."""
        # Remove DEMO_MODE from environment if it exists
        with patch.dict(os.environ, {}, clear=False):
            if "DEMO_MODE" in os.environ:
                del os.environ["DEMO_MODE"]

            db_alias = self.router.db_for_read(None)
            self.assertEqual(db_alias, "default")

    def test_allow_relation_same_database_set(self):
        """Test that relations are allowed between objects in the same database set."""

        # Mock objects with database state
        class MockObj:
            def __init__(self, db):
                self._state = type("MockState", (), {"db": db})()

        obj1 = MockObj("default")
        obj2 = MockObj("default")

        # Both are in the allowed database set
        result = self.router.allow_relation(obj1, obj2)
        self.assertTrue(result)

    def test_allow_relation_different_database_set(self):
        """Test that relations return None for objects outside the database set."""

        class MockObj:
            def __init__(self, db):
                self._state = type("MockState", (), {"db": db})()

        obj1 = MockObj("default")
        obj2 = MockObj("other_db")

        # One is outside the allowed database set
        result = self.router.allow_relation(obj1, obj2)
        self.assertIsNone(result)

    def test_allow_migrate_valid_databases(self):
        """Test that migrations are allowed on valid databases."""
        # Test default database
        result = self.router.allow_migrate("default", "stonks_overwatch")
        self.assertTrue(result)

        # Test demo database
        result = self.router.allow_migrate("demo", "stonks_overwatch")
        self.assertTrue(result)

    def test_get_database_alias_internal_method(self):
        """Test the internal _get_database_alias method directly."""
        # Test production mode
        with patch.dict(os.environ, {"DEMO_MODE": "False"}, clear=False):
            alias = self.router._get_database_alias()
            self.assertEqual(alias, "default")

        # Test demo mode
        with patch.dict(os.environ, {"DEMO_MODE": "True"}, clear=False):
            alias = self.router._get_database_alias()
            self.assertEqual(alias, "demo")
