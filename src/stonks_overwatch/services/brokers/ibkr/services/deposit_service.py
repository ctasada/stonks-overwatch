"""
IBKR Deposit Service Implementation.

This service provides deposit/withdrawal tracking for IBKR accounts.
Currently returns empty data as IBKR doesn't provide direct deposit tracking
through their API in the same way as other brokers.
"""

from typing import Dict, List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.models import Deposit
from stonks_overwatch.utils.core.logger import StonksLogger


class DepositsService(BaseService, DepositServiceInterface):
    """
    IBKR Deposit Service Implementation.

    This service handles deposit and withdrawal tracking for IBKR accounts.
    Currently provides minimal implementation as IBKR doesn't expose
    deposit/withdrawal data through their API in the same format as other brokers.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """
        Initialize the IBKR deposits service.

        Args:
            config: Optional broker configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[IBKR|DEPOSITS]")
        self.ibkr_service = IbkrService()

    @property
    def broker_name(self) -> BrokerName:
        """Return the broker name."""
        return BrokerName.IBKR

    def get_cash_deposits(self) -> List[Deposit]:
        """
        Retrieves the cash deposit and withdrawal history.

        Note: IBKR doesn't provide direct deposit/withdrawal tracking through their API
        in the same format as other brokers. This method returns an empty list.
        Users should track deposits/withdrawals manually or through IBKR's web interface.

        Returns:
            List[Deposit]: Empty list as IBKR doesn't support direct deposit tracking
        """
        self.logger.debug("Getting cash deposits for IBKR")
        self.logger.info("IBKR deposit tracking not supported - returning empty list")
        return []

    def calculate_cash_account_value(self) -> Dict[str, float]:
        """
        Calculates the cash account value over time.

        Note: IBKR doesn't provide historical cash balance data through their API
        in the same format as other brokers. This method returns an empty dictionary.

        Returns:
            Dict[str, float]: Empty dictionary as IBKR doesn't support historical cash tracking
        """
        self.logger.debug("Calculating cash account value for IBKR")
        self.logger.info("IBKR historical cash tracking not supported - returning empty dict")
        return {}
