"""
MetaTrader 4 Fee Service Implementation.

This service provides fee tracking for MT4 accounts.
MT4 includes fees (commission, swap, taxes) directly in transaction records,
so separate fee tracking is not needed.
"""

from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.fee_service import FeeServiceInterface
from stonks_overwatch.services.models import Fee
from stonks_overwatch.utils.core.logger import StonksLogger


class FeeService(BaseService, FeeServiceInterface):
    """
    MetaTrader 4 Fee Service Implementation.

    This service handles fee tracking for MT4 accounts.
    MT4 includes all fees (commission, swap, taxes) directly in the
    transaction records, so separate fee tracking is not necessary.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """
        Initialize the MT4 fee service.

        Args:
            config: Optional broker configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|FEES]")

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return BrokerName.METATRADER4

    def get_fees(self) -> List[Fee]:
        """
        Retrieves the fee history including transaction fees, account fees, and other charges.

        Note: MT4 includes all fees (commission, swap, taxes) directly in the
        transaction records. Access fees through the transaction service instead.
        This method returns an empty list.

        Returns:
            List[Fee]: Empty list as MT4 includes fees in transaction records
        """
        self.logger.debug("Getting fees for MetaTrader 4")
        self.logger.info("MT4 fee tracking not needed - fees are included in transaction records")
        return []
