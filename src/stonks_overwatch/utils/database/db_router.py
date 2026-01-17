"""
Database router for Stonks Overwatch application.

This router automatically selects the appropriate database (production or demo)
based on the DEMO_MODE environment variable, eliminating the need to restart
Django when switching between databases.
"""

from stonks_overwatch.utils.core.logger import StonksLogger


class DatabaseRouter:
    """
    A router to control all database operations on models for different databases.

    This router directs all database operations to either the 'default' database
    or the 'demo' database based on the DEMO_MODE environment variable.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.utils", "[DB_ROUTER]")

    def _get_database_alias(self):
        """
        Determine which database to use based on demo mode status.

        Returns:
            str: 'demo' if demo mode is enabled, 'default' otherwise
        """
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        demo_mode = is_demo_mode()

        return "demo" if demo_mode else "default"

    def db_for_read(self, model, **hints):
        """
        Suggest the database to read from for objects of type model.

        Args:
            model: The model class
            **hints: Additional hints for database selection

        Returns:
            str: Database alias to use for reading
        """
        return self._get_database_alias()

    def db_for_write(self, model, **hints):
        """
        Suggest the database to write to for objects of type model.

        Args:
            model: The model class
            **hints: Additional hints for database selection

        Returns:
            str: Database alias to use for writing
        """
        return self._get_database_alias()

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if models are in the same database.

        Args:
            obj1: First model instance
            obj2: Second model instance
            **hints: Additional hints for relation checking

        Returns:
            bool: True if relation is allowed, None if no opinion
        """
        if obj1._state.db == obj2._state.db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # noqa: ARG002
        """
        Ensure that certain apps' models get created on the right database.

        Args:
            db: Database alias
            app_label: Application label (unused but required by Django interface)
            model_name: Model name (unused but required by Django interface)
            **hints: Additional hints for migration

        Returns:
            bool: True if migration is allowed, False otherwise
        """
        return True
