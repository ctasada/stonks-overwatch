"""
Logger constants for consistent logging across the application.

This module provides constants for logger names and tags to reduce duplication
and ensure consistency across the codebase.
"""

# Logger domains
LOGGER_CONFIG = "stonks_overwatch.config"
LOGGER_CORE = "stonks_overwatch.core"
LOGGER_SERVICES = "stonks_overwatch.services"

# Logger tags
TAG_CONFIG = "[CONFIG]"
TAG_BASE_CONFIG = "[BASE_CONFIG]"
TAG_BROKER_FACTORY = "[BROKER_FACTORY]"
TAG_BROKER_REGISTRY = "[BROKER_REGISTRY]"
TAG_GLOBAL_CONFIG = "[GLOBAL_CONFIG]"
