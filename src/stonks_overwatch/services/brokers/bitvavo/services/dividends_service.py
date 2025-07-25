from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces import DividendServiceInterface
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.models import Dividend
from stonks_overwatch.utils.core.logger import StonksLogger


class DividendsService(BaseService, DividendServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.dividends_service", "[BITVAVO|DIVIDENDS]")

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)

    def get_dividends(self) -> List[Dividend]:
        """
        Bitvavo does not support dividends, so this method returns an empty list.
        """
        return []
