import os
import tempfile
from functools import wraps

import requests_cache

import pytest


@pytest.fixture(scope="session")
def temp_cache_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "test_cache.sqlite")
        print(f"Temporary cache path: {temp_db_path}")
        yield temp_db_path
    print("Temporary directory cleaned up")


def create_patched_enabled(original_enabled, temp_cache_path):
    @wraps(original_enabled)
    def patched_enabled(*args, **kwargs):
        # Override the cache_name if it's provided
        kwargs["cache_name"] = temp_cache_path
        # Ensure we're using the sqlite backend
        kwargs["backend"] = "sqlite"
        return original_enabled(*args, **kwargs)

    return patched_enabled


@pytest.fixture(autouse=True)
def use_temp_cache(temp_cache_path, monkeypatch):
    original_enabled = requests_cache.enabled
    patched_enabled = create_patched_enabled(original_enabled, temp_cache_path)
    monkeypatch.setattr(requests_cache, "enabled", patched_enabled)
    print("Patched requests_cache.enabled to use temporary cache")

    # Clear the cache before and after each test
    requests_cache.clear()
    yield
    requests_cache.clear()


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset the global configuration before each test to ensure clean state."""
    from stonks_overwatch.config.global_config import global_config

    # Reset the global config to force reload
    global_config.reset_for_tests()
    yield
