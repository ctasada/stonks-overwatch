from typing import List

from stonks_overwatch.core.interfaces import DividendServiceInterface
from stonks_overwatch.services.models import Dividend
from stonks_overwatch.utils.core.logger import StonksLogger


class DividendsService(DividendServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.dividends_service", "[DEGIRO|DIVIDENDS]")

    def get_dividends(self) -> List[Dividend]:
        """
        Bitvavo does not support dividends, so this method returns an empty list.
        """
        return []
