import time
from typing import List, Optional

from django.utils import timezone
from django.utils.functional import cached_property
from iso10383 import MIC

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.ibkr.client.constants import AssetClass
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.brokers.ibkr.repositories.positions_repository import PositionsRepository
from stonks_overwatch.services.models import Country, DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType, Sector


class PortfolioService(BaseService, PortfolioServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.portfolio_data.ibkr", "[IBKR|PORTFOLIO]")

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.positions_repository = PositionsRepository()
        self.ibkr_service = IbkrService()
        # Use base_currency property from BaseService which handles dependency injection
        # self.base_currency = self.base_currency  # This will use the property from BaseService

    @cached_property
    def get_portfolio(self) -> List[PortfolioEntry]:
        self.logger.debug("Get Portfolio")

        all_positions = self.positions_repository.get_all_positions()

        # IBKR API requires querying /accounts before /account/{id}/summary
        # This ensures the session is properly initialized
        self.ibkr_service.get_portfolio_accounts()

        # Add a small delay to ensure the API session is ready
        time.sleep(0.2)

        # Try to get account summary with retry logic
        account_summary = None
        base_currency = self.ibkr_service.get_default_currency()
        max_retries = 2

        for attempt in range(max_retries):
            try:
                account_summary = self.ibkr_service.get_account_summary()
                break
            except Exception as e:
                error_msg = str(e).lower()
                if "please query /accounts first" in error_msg and attempt < max_retries - 1:
                    self.logger.warning(
                        f"IBKR API session not ready (attempt {attempt + 1}/{max_retries}), retrying after delay..."
                    )
                    # Call /accounts again and wait a bit longer
                    self.ibkr_service.get_portfolio_accounts()
                    time.sleep(0.5)
                else:
                    self.logger.error(f"Failed to get account summary after {attempt + 1} attempts: {e}")
                    # Continue without account summary - we'll skip cash balances
                    break

        portfolio = []

        for position in all_positions:
            try:
                self.logger.debug(f"Position: {position}")
                entry = self.__create_portfolio_entry(position, base_currency)
                portfolio.append(entry)
            except Exception as e:
                self.logger.error(f"Error creating portfolio entry for position {position.get('ticker', '')}: {e}")

        # Only process cash balances if we successfully got the account summary
        if account_summary:
            for cash_balance in account_summary["cashBalances"]:
                if cash_balance["currency"] in ["USD", "EUR"]:
                    value = cash_balance["balance"]
                    currency = cash_balance["currency"]
                    base_currency_value = self.ibkr_service.convert_to_default_currency(currency, value)

                    entry = PortfolioEntry(
                        name=f"Cash Balance {cash_balance['currency']}",
                        symbol=cash_balance["currency"],
                        product_type=ProductType.CASH,
                        product_currency=currency,
                        value=value,
                        base_currency_value=base_currency_value,
                        base_currency=base_currency,
                        is_open=True,
                    )
                    portfolio.append(entry)
        else:
            self.logger.warning("Skipping cash balances - account summary not available")

        return sorted(portfolio, key=lambda k: k.symbol)

    def __create_portfolio_entry(self, position: dict, base_currency: str) -> PortfolioEntry:
        """
        Create a portfolio entry from IBKR position data.

        Note: Some fields (sector, group) are genuinely None for ETFs.
        Others (ticker, name, type, etc.) are populated after the gateway cache warms up.
        Defensive fallbacks handle both cases. See docs/IBKR.md for details.

        Args:
            position: Position data from IBKR (may contain None values)
            base_currency: Base currency for conversions

        Returns:
            PortfolioEntry with defensive fallback values
        """
        currency = position["currency"]
        price = self.__get_last_quotation(position)
        value = position["position"] * price
        break_even_price = position["avgPrice"]
        base_currency_price = self.ibkr_service.convert_to_default_currency(currency, price)
        base_currency_break_even_price = self.ibkr_service.convert_to_default_currency(currency, break_even_price)
        base_currency_value = self.ibkr_service.convert_to_default_currency(currency, value)

        unrealized_gain = position["unrealizedPnl"]
        total_realized_gains = position["realizedPnl"]
        avg_price = (
            position["baseAvgPrice"]
            if ("baseAvgPrice" in position and position["baseAvgPrice"])
            else position["avgPrice"]
        )
        total_costs = position["position"] * avg_price

        is_open = position["position"] > 0

        # Defensive handling: ETFs have null sector/group; use contractDesc as ticker fallback
        ticker = position.get("ticker") or position.get("contractDesc") or "UNKNOWN"
        name = position.get("name") or position.get("contractDesc") or ticker
        sector_str = position.get("sector") or "Unknown"
        industry = position.get("group") or "Others"
        listing_exchange = position.get("listingExchange")
        country_code = position.get("countryCode") or "US"

        return PortfolioEntry(
            name=name,
            symbol=ticker,
            sector=Sector.from_str(sector_str),
            industry=industry,
            # FIXME: Add stock class category
            exchange=self.__find_exchange(listing_exchange) if listing_exchange else None,
            country=Country(country_code),
            product_type=self.__get_product_type(position),
            shares=position["position"],
            product_currency=currency,
            price=price,
            base_currency_price=base_currency_price,
            base_currency=base_currency,
            break_even_price=break_even_price,
            base_currency_break_even_price=base_currency_break_even_price,
            value=value,
            base_currency_value=base_currency_value,
            is_open=is_open,
            unrealized_gain=unrealized_gain,
            realized_gain=total_realized_gains,
            total_costs=total_costs,
        )

    def __find_exchange(self, acronym: str) -> MIC | None:
        # FIXME: Special Mapping for some exchanges
        if acronym in ["BM"]:
            return MIC.xmad.value
        elif acronym in ["PINK"]:
            return MIC.pinx.value
        elif acronym in ["LSEETF"]:
            return MIC.xlon.value
        elif acronym in ["IBIS", "IBIS2"]:
            return MIC.xetr.value

        if hasattr(MIC, acronym.lower()):
            return MIC[acronym.lower()].value

        for exchange in MIC:
            if exchange.value.acronym == acronym:
                return exchange.value

        self.logger.warning(f"Unknown Exchange code: {acronym}")
        return None

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        self.logger.debug("Get Portfolio Total")

        # Calculate current value
        if not portfolio:
            portfolio = self.get_portfolio

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            if entry.is_open:
                portfolio_total_value += entry.base_currency_value
                # tmp_total_portfolio[entry.name] = entry.base_currency_value

        # FIXME: The value needs to be properly retrieved from IBKR
        tmp_total_portfolio["totalDepositWithdrawal"] = 10000.0
        tmp_total_portfolio["totalCash"] = self.__get_total_cash()
        # DISABLED UNTIL WE HAVE A WAY TO CACHE THE IBKR DATA
        # tmp_total_portfolio["totalDepositWithdrawal"] = CashMovementsRepository.get_total_cash_deposits_raw()
        # tmp_total_portfolio["totalCash"] = CashMovementsRepository.get_total_cash()
        #
        # # Try to get the data directly from IBKR, so we get up-to-date values
        # realtime_total_portfolio = self.__get_realtime_portfolio_total()
        # if realtime_total_portfolio:
        #     tmp_total_portfolio = realtime_total_portfolio

        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        return TotalPortfolio(
            base_currency=self.base_currency,
            total_pl=total_profit_loss,
            total_cash=tmp_total_portfolio["totalCash"],
            current_value=portfolio_total_value,
            total_roi=roi,
            total_deposit_withdrawal=tmp_total_portfolio["totalDepositWithdrawal"],
        )

    def __get_total_cash(self) -> float:
        # IBKR API requires querying /accounts before /account/{id}/summary
        # This ensures the session is properly initialized
        self.ibkr_service.get_portfolio_accounts()

        # Add a small delay to ensure the API session is ready
        time.sleep(0.2)

        # Try to get account summary with retry logic
        max_retries = 2

        for attempt in range(max_retries):
            try:
                account_summary = self.ibkr_service.get_account_summary()

                for cash_balance in account_summary["cashBalances"]:
                    if cash_balance["currency"].startswith("Total "):
                        return cash_balance["balance"]

                raise ValueError("Total cash balance not found in IBKR account summary")

            except Exception as e:
                error_msg = str(e).lower()
                if "please query /accounts first" in error_msg and attempt < max_retries - 1:
                    self.logger.warning(
                        f"IBKR API session not ready (attempt {attempt + 1}/{max_retries}), retrying after delay..."
                    )
                    # Call /accounts again and wait a bit longer
                    self.ibkr_service.get_portfolio_accounts()
                    time.sleep(0.5)
                else:
                    self.logger.error(f"Failed to get total cash after {attempt + 1} attempts: {e}")
                    # Return 0 as fallback
                    return 0.0

        # Fallback in case loop completes without return
        return 0.0

    def __get_last_quotation(self, position: dict) -> float:
        # FIXME: Retrieving the last 5 days to guarantee we have a value (for example on Mondays). There may be a better
        #  way to do this.
        try:
            conid = position["conid"]
            history = self.ibkr_service.client.marketdata_history_by_conid(
                conid=conid, period="5d", bar="1d", outside_rth=True
            ).data
            return history["data"][-1]["c"]
        except Exception:
            self.logger.warning(f"Error retrieving last quotation for position {position.get('ticker', '')}")
            return position["mktPrice"]

    @staticmethod
    def __get_product_type(position: dict) -> ProductType:
        # FIXME: Create an Enum for the product types
        if position["type"] == "ETF":
            return ProductType.ETF

        if AssetClass.from_string(position["assetClass"]) == AssetClass.STOCK:
            return ProductType.STOCK

        raise ValueError(f"Unknown product type: {position['type']} / {position['assetClass']}")

    def calculate_historical_value(self) -> List[DailyValue]:
        """
        Calculates the historical portfolio value over time.

        Note: IBKR doesn't provide easy access to historical portfolio values.
        This implementation returns a minimal dataset with current portfolio value
        to prevent dashboard errors.

        Returns:
            List[DailyValue]: List containing current portfolio value
        """
        self.logger.debug("Calculating historical value for IBKR")

        try:
            # Get current portfolio total
            portfolio_total = self.get_portfolio_total()
            current_date = timezone.now().strftime("%Y-%m-%d")

            # Return minimal historical data with current value
            return [DailyValue(x=current_date, y=portfolio_total.current_value)]
        except Exception as e:
            self.logger.error(f"Error calculating historical value: {e}")
            # Return empty list as fallback
            return []

    def calculate_product_growth(self) -> dict:
        # TODO: Implement product growth calculation
        pass
