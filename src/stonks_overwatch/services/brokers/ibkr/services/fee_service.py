"""
IBKR Fee Service Implementation.

This service provides fee tracking for IBKR accounts.
Currently returns empty data as IBKR doesn't provide direct fee tracking
through their API in the same way as other brokers.
"""

from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.fee_service import FeeServiceInterface
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.models import Fee
from stonks_overwatch.utils.core.logger import StonksLogger


class FeeService(BaseService, FeeServiceInterface):
    """
    IBKR Fee Service Implementation.

    This service handles fee tracking for IBKR accounts.
    Currently provides minimal implementation as IBKR doesn't expose
    fee data through their API in the same format as other brokers.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """
        Initialize the IBKR fee service.

        Args:
            config: Optional broker configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[IBKR|FEES]")
        self.ibkr_service = IbkrService()

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return "ibkr"

    def get_fees(self) -> List[Fee]:
        """
        Retrieves the fee history including transaction fees, account fees, and other charges.

        Note: IBKR doesn't provide direct fee tracking through their API
        in the same format as other brokers. This method returns an empty list.
        Users should track fees manually or through IBKR's web interface.

        Returns:
            List[Fee]: Empty list as IBKR doesn't support direct fee tracking
        """
        self.logger.debug("Getting fees for IBKR")
        self.logger.info("IBKR fee tracking not supported - returning empty list")
        return []
