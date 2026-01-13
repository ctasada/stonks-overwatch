from functools import wraps
from threading import Lock
from typing import Any, TypeVar

T = TypeVar("T")

# Global registry to track singleton instances for reset functionality
_singleton_instances: dict[type, Any] = {}
_singleton_locks: dict[type, Lock] = {}


def singleton(cls: type[T]) -> type[T]:
    """
    A thread-safe singleton decorator that works with any Python class.
    Ensures only one instance of the decorated class is created.

    Args:
        cls: The class to be made into a singleton

    Returns:
        The decorated class with singleton behavior

    Example:
        @singleton
        class MyClass:
            def __init__(self, value: int):
                self.value = value

        # Creates only one instance
        instance1 = MyClass(1)
        instance2 = MyClass(2)  # Returns existing instance
        assert instance1 is instance2
    """

    original_new = cls.__new__
    original_init = cls.__init__

    # Register the singleton in the global registry
    _singleton_instances[cls] = None
    _singleton_locks[cls] = Lock()

    # Reference the lock from the registry
    lock = _singleton_locks[cls]

    @wraps(cls.__new__)
    def __new__(cls_: type[T], *args: Any, **kwargs: Any) -> T:  # noqa: N807
        """
        Override of __new__ to implement the singleton pattern.

        This method ensures only one instance of the class is created and
        returned, regardless of how many times the class is instantiated.

        Args:
            cls_: The class being instantiated
            *args: Positional arguments passed to the class constructor
            **kwargs: Keyword arguments passed to the class constructor

        Returns:
            The single instance of the class

        Thread Safety:
            Uses a threading.Lock to ensure thread-safe instance creation
        """
        with lock:
            if _singleton_instances[cls] is None:
                _singleton_instances[cls] = original_new(cls_)
                _singleton_instances[cls]._singleton_class = cls_
            return _singleton_instances[cls]

    @wraps(cls.__init__)
    def __init__(self: T, *args: Any, **kwargs: Any) -> None:  # noqa: N807
        """
        Override of __init__ to prevent multiple initializations.

        This method ensures the initialization code is only run once
        for the singleton instance, even if the class constructor is
        called multiple times.

        Args:
            self: The singleton instance
            *args: Positional arguments passed to the constructor
            **kwargs: Keyword arguments passed to the constructor

        Note:
            Subsequent calls to __init__ on the same instance will be ignored
            to prevent re-initialization of the singleton.
        """
        if not hasattr(self, "_initialized"):
            original_init(self, *args, **kwargs)
            self._initialized = True

    # Override class methods
    cls.__new__ = __new__
    cls.__init__ = __init__

    return cls


def reset_singleton(cls: type[T]) -> None:
    """
    Reset a singleton instance, forcing it to be recreated on next access.

    This is useful when you need to reinitialize a singleton with updated
    configuration or credentials.

    Args:
        cls: The singleton class to reset

    Example:
        @singleton
        class ConfigService:
            def __init__(self):
                self.config = load_config()

        # Use the service
        service = ConfigService()

        # Update config file...

        # Reset the singleton to reload config
        reset_singleton(ConfigService)

        # Next access will create a new instance with fresh config
        service = ConfigService()

    Thread Safety:
        Uses the singleton's lock to ensure thread-safe reset
    """
    if cls not in _singleton_instances:
        raise ValueError(f"Class {cls.__name__} is not registered as a singleton")

    lock = _singleton_locks[cls]
    with lock:
        if _singleton_instances[cls] is not None:
            # Clean up the old instance
            old_instance = _singleton_instances[cls]
            if hasattr(old_instance, "_initialized"):
                delattr(old_instance, "_initialized")
            if hasattr(old_instance, "_singleton_class"):
                delattr(old_instance, "_singleton_class")

        # Reset the instance to None
        _singleton_instances[cls] = None
