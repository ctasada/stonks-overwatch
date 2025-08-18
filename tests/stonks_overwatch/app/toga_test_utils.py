"""
Toga-specific test utilities for stonks-overwatch app tests.

This module provides reusable utilities for testing Toga GUI components,
particularly for handling conditional imports when toga is not available
in CI environments.
"""

import importlib.util
from typing import Any, Dict

import pytest


def is_toga_available() -> bool:
    """
    Check if toga is available for import.

    Returns:
        bool: True if toga can be imported, False otherwise
    """
    return importlib.util.find_spec("toga") is not None


# Shared pytest mark for skipping toga tests when toga is not available
skip_if_toga_unavailable = pytest.mark.skipif(not is_toga_available(), reason="toga not available")


def conditional_import(module_name: str, from_module: str, fallback: Any = None) -> Any:
    """
    Conditionally import a class/function only if toga is available.

    Args:
        module_name: The name of the module/class to import
        from_module: The module path to import from
        fallback: Value to return if toga is not available (default: None)

    Returns:
        The imported class/function if toga is available, otherwise fallback

    Example:
        StonksOverwatchApp = conditional_import(
            "StonksOverwatchApp",
            "stonks_overwatch.app.main"
        )
    """
    if is_toga_available():
        try:
            module = importlib.import_module(from_module)
            return getattr(module, module_name)
        except (ImportError, AttributeError):
            return fallback
    return fallback


def conditional_imports(imports_dict: Dict[str, str], fallback: Any = None) -> Dict[str, Any]:
    """
    Conditionally import multiple classes/functions if toga is available.

    Args:
        imports_dict: Dictionary mapping import names to module paths
        fallback: Value to use for all imports if toga is not available

    Returns:
        Dictionary with imported classes or fallback values

    Example:
        imports = conditional_imports({
            "StonksOverwatchApp": "stonks_overwatch.app.main",
            "DialogManager": "stonks_overwatch.app.dialogs.dialogs"
        })
        StonksOverwatchApp = imports["StonksOverwatchApp"]
    """
    result = {}
    for import_name, module_path in imports_dict.items():
        result[import_name] = conditional_import(import_name, module_path, fallback)
    return result


# Pre-computed availability for module-level use
TOGA_AVAILABLE = is_toga_available()
