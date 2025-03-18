from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class BaseCredentials:
    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseCredentials":
        return cls(**data)
