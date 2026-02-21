from abc import ABC, abstractmethod

from stonks_overwatch.integrations.logos.types import LogoType


class LogoIntegration(ABC):
    @abstractmethod
    def supports(self, logo_type: LogoType) -> bool: ...

    @abstractmethod
    def get_logo_url(self, logo_type: LogoType, symbol: str, theme: str = "light", isin: str = "") -> str: ...
