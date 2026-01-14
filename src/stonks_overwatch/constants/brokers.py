"""Broker name constants for type-safe broker identification."""

from enum import Enum, unique
from typing import List, Union


@unique
class BrokerName(str, Enum):
    """Standardized broker name constants with display metadata.

    This enum provides type-safe broker name constants to:
    - Eliminate typo bugs from hardcoded strings
    - Improve IDE autocomplete support
    - Enable better type safety with type hints
    - Provide helper methods for common operations
    - Provide display names for UI rendering
    - Guarantee no duplicate values (@unique decorator)

    Each broker has:
    - value: Technical identifier (e.g., "degiro")
    - short_name: Compact display name (e.g., "IBKR")
    - long_name: Full display name (e.g., "Interactive Brokers")
    - display_name: Alias for long_name (primary display name)

    Since this enum inherits from str, it can be used directly where strings
    are expected, but for explicit string conversion use .value attribute.

    The @unique decorator ensures no duplicate broker values can be defined,
    preventing configuration errors at import time.

    Example:
        >>> if broker_name == BrokerName.DEGIRO:
        >>>     # Type-safe comparison
        >>>     pass
        >>>
        >>> # Get display names
        >>> broker = BrokerName.IBKR
        >>> broker.value           # "ibkr"
        >>> broker.short_name      # "IBKR"
        >>> broker.long_name       # "Interactive Brokers"
        >>> broker.display_name    # "Interactive Brokers"
        >>>
        >>> # Debugging representation
        >>> repr(BrokerName.IBKR)  # "BrokerName.IBKR"
        >>>
        >>> # Normalize string to enum
        >>> broker = BrokerName.from_string("degiro")
    """

    DEGIRO = "degiro"
    BITVAVO = "bitvavo"
    IBKR = "ibkr"

    @property
    def short_name(self) -> str:
        """Get the short display name for compact UI contexts.

        Returns:
            Short name suitable for buttons, tabs, labels

        Example:
            >>> BrokerName.IBKR.short_name
            'IBKR'
        """
        _short_names = {
            BrokerName.DEGIRO: "DEGIRO",
            BrokerName.BITVAVO: "Bitvavo",
            BrokerName.IBKR: "IBKR",
        }
        return _short_names.get(self, self.value.upper())

    @property
    def long_name(self) -> str:
        """Get the full display name for descriptive UI contexts.

        Returns:
            Full official name of the broker

        Example:
            >>> BrokerName.IBKR.long_name
            'Interactive Brokers'
        """
        _long_names = {
            BrokerName.DEGIRO: "DEGIRO",
            BrokerName.BITVAVO: "Bitvavo",
            BrokerName.IBKR: "Interactive Brokers",
        }
        return _long_names.get(self, self.value.title())

    @property
    def display_name(self) -> str:
        """Alias for long_name - the primary display name.

        Returns:
            Full display name (same as long_name)

        Example:
            >>> BrokerName.DEGIRO.display_name
            'DEGIRO'
        """
        return self.long_name

    @classmethod
    def from_string(cls, value: str) -> "BrokerName":
        """Convert a string to BrokerName enum.

        Args:
            value: Broker name as string

        Returns:
            BrokerName enum value

        Raises:
            ValueError: If broker name is not valid

        Example:
            >>> broker = BrokerName.from_string("degiro")
            >>> assert broker == BrokerName.DEGIRO
        """
        try:
            return cls(value.lower())
        except ValueError as e:
            raise ValueError(f"Invalid broker name: {value}. Valid options: {cls.all()}") from e

    @classmethod
    def all(cls) -> List[str]:
        """Get list of all broker names.

        Returns:
            List of broker name strings

        Example:
            >>> BrokerName.all()
            ['degiro', 'bitvavo', 'ibkr']
        """
        return [broker.value for broker in cls]

    @classmethod
    def normalize(cls, broker: Union["BrokerName", str]) -> str:
        """Normalize broker input to string value.

        Accepts both BrokerName enum and string, returns string value.
        This is a convenience method for functions that accept both types.

        Args:
            broker: Broker name (can be string or BrokerName enum)

        Returns:
            Broker name as string

        Example:
            >>> BrokerName.normalize(BrokerName.DEGIRO)
            'degiro'
            >>> BrokerName.normalize("degiro")
            'degiro'
        """
        return broker.value if isinstance(broker, cls) else broker

    @classmethod
    def is_valid(cls, broker: str) -> bool:
        """Check if broker name is valid.

        Args:
            broker: Broker name to validate

        Returns:
            True if broker name is valid, False otherwise

        Example:
            >>> BrokerName.is_valid("degiro")
            True
            >>> BrokerName.is_valid("invalid_broker")
            False
        """
        return broker in cls.all()

    def __str__(self) -> str:
        """Return string value of broker name."""
        return self.value

    def __repr__(self) -> str:
        """Return unambiguous string representation for debugging.

        Returns:
            String in format "BrokerName.MEMBER_NAME"

        Example:
            >>> repr(BrokerName.IBKR)
            'BrokerName.IBKR'
        """
        return f"{self.__class__.__name__}.{self.name}"
