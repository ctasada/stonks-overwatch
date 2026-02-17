from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BaseCredentials(ABC):
    """
    Base class for broker credentials.

    All credential classes must implement:
    - to_auth_params(): Convert credentials to authentication parameters
    """

    def to_dict(self) -> dict:
        """
        Convert credentials to a dictionary containing all fields.

        Returns:
            Dictionary with all credential fields
        """
        return self.__dict__

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseCredentials":
        """
        Create credentials instance from a dictionary.

        Args:
            data: Dictionary containing credential fields

        Returns:
            Credentials instance
        """
        return cls(**data)

    @abstractmethod
    def to_auth_params(self) -> dict:
        """
        Convert credentials to authentication parameters.

        This method must be implemented by all credential classes to provide
        the specific parameters needed for their authentication service.

        Returns:
            Dictionary with authentication parameters for the broker's auth service

        Note:
            This method should return only the fields needed for authentication,
            potentially with field name transformations (e.g., apikey → api_key).
            The remember_me parameter should be omitted as it's only relevant
            during initial manual login, not auto-authentication.
        """
        pass
