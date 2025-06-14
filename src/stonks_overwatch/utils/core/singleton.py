from functools import wraps
from threading import Lock
from typing import Any, TypeVar

T = TypeVar("T")


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

    instance = None
    lock = Lock()

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
        nonlocal instance

        with lock:
            if instance is None:
                instance = original_new(cls_)
                instance._singleton_class = cls_
            return instance

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
