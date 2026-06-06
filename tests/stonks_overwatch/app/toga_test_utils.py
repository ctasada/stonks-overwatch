"""
Toga-specific test utilities for stonks-overwatch app tests.

This module provides reusable utilities for testing Toga GUI components,
particularly for handling conditional imports when toga is not available
in CI environments.
"""

import importlib.util
import sys
from typing import Any, Dict

import pytest


def is_toga_available() -> bool:
    """
    Check if toga is available *and* safe to instantiate in this environment.

    Returning True when toga is installed but cannot be used causes a fatal
    process abort on macOS: toga_cocoa's App.__init__ calls into
    NSApplication which requires a running main run loop.  In a headless
    pytest session that run loop is never started, so we probe for it via
    rubicon-objc before declaring toga usable.

    Returns:
        bool: True only when toga can be safely instantiated in this process
    """
    if importlib.util.find_spec("toga") is None:
        return False

    if sys.platform == "darwin":
        # toga_cocoa delegates to NSApplication.  If the shared application
        # is not yet running (headless pytest, CI, terminal), instantiating
        # toga.App will call `Abort` and kill the entire test process.
        try:
            from rubicon.objc import ObjCClass  # type: ignore[import-untyped]

            ns_app = ObjCClass("NSApplication").sharedApplication
            return bool(ns_app.isRunning)
        except Exception:
            return False

    return True


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
