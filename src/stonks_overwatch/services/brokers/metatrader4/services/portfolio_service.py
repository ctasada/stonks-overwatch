from datetime import date
from typing import List, Optional

import polars as pl
from currency_converter import CurrencyConverter

from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.brokers.metatrader4.services.deposit_service import DepositService
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType


class PortfolioService(BaseService, PortfolioServiceInterface):
    # Display constants
    CASH_BALANCE_NAME_TEMPLATE = "Cash Balance {currency}"

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|PORTFOLIO]")
        self.repository = Metatrader4Repository()
        self.deposit_service = DepositService()
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.currency = self.repository.get_account_currency()

    @property
    def get_portfolio(self) -> List[PortfolioEntry]:
        """Return portfolio data for this broker from the database."""
        self.logger.debug("Fetching portfolio data from database")

        portfolio_entries = []

        summary = self.repository.get_latest_summary()
        if summary.balance:
            base_currency_value = self.currency_converter.convert(
                float(summary.balance), self.currency, self.base_currency, date.today()
            )
            portfolio_entries.append(
                PortfolioEntry(
                    name=self.CASH_BALANCE_NAME_TEMPLATE.format(currency=self.currency),
                    symbol=self.currency,
                    product_type=ProductType.CASH,
                    product_currency=self.currency,
                    value=float(summary.balance),
                    base_currency_value=base_currency_value,
                    base_currency=self.base_currency,
                    is_open=True,
                )
            )

        self.logger.debug(f"Retrieved {len(portfolio_entries)} portfolio entries from database")
        return portfolio_entries

    def _calculate_roi(self, summary) -> float:
        """
        Calculate Return on Investment (ROI) based on MT4 summary data.

        Args:
            summary: Metatrader4Summary object containing account data

        Returns:
            ROI as a percentage (e.g., 15.5 for 15.5%)
        """
        if not summary or not summary.deposit_withdrawal:
            return 0.0

        deposit_withdrawal = float(summary.deposit_withdrawal)
        if deposit_withdrawal == 0:
            return 0.0

        closed_trade_pl = float(summary.closed_trade_pl) if summary.closed_trade_pl else 0.0

        # ROI = (Closed Gain/Loss / Net Deposits) * 100
        total_roi = (closed_trade_pl / abs(deposit_withdrawal)) * 100.0

        return total_roi

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        """
        Calculate total portfolio value.

        Args:
            portfolio: Optional portfolio entries (uses get_portfolio if not provided)

        Returns:
            TotalPortfolio with calculated totals
        """
        # Get account summary for additional data
        total_roi = 0.0
        total_pl = 0.0
        total_cash = 0.0
        current_value = 0.0
        total_deposit_withdrawal = 0.0

        try:
            summary = self.repository.get_latest_summary()
            if summary:
                total_roi = self._calculate_roi(summary)

                if summary.floating_pl:
                    total_pl = self.currency_converter.convert(
                        float(summary.closed_trade_pl), self.currency, self.base_currency, date.today()
                    )
                if summary.equity:
                    total_cash = self.currency_converter.convert(
                        float(summary.equity), self.currency, self.base_currency, date.today()
                    )
                if summary.balance:
                    current_value = self.currency_converter.convert(
                        float(summary.balance), self.currency, self.base_currency, date.today()
                    )
                if summary.deposit_withdrawal:
                    total_deposit_withdrawal = self.currency_converter.convert(
                        float(summary.deposit_withdrawal), self.currency, self.base_currency, date.today()
                    )
        except Exception as e:
            self.logger.warning(f"Failed to get summary data: {e}")

        return TotalPortfolio(
            base_currency=self.base_currency,
            total_pl=total_pl,
            total_cash=total_cash,
            current_value=current_value,
            total_roi=total_roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )

    def calculate_historical_value(self) -> List[DailyValue]:
        self.logger.debug("Calculating historical value")

        deposits = self.deposit_service.get_cash_deposits()
        trades = self.repository.get_closed_trades()

        try:
            # Prepare deposit data with currency conversion
            deposit_data = []
            for deposit in deposits:
                if deposit.datetime:
                    date_key = deposit.datetime.date()
                    change_in_base = self.currency_converter.convert(
                        deposit.change, deposit.currency, self.base_currency, date_key
                    )
                    deposit_data.append({"date": date_key, "value": change_in_base})

            # Prepare trade data with currency conversion
            trade_data = []
            for trade in trades:
                if trade.close_time and trade.profit:
                    date_key = trade.close_time.date()
                    profit_in_base = self.currency_converter.convert(
                        float(trade.profit), self.currency, self.base_currency, date_key
                    )
                    trade_data.append({"date": date_key, "value": profit_in_base})

            # Combine deposits and trades into a single dataframe
            combined_data = deposit_data + trade_data

            if not combined_data:
                self.logger.debug("No deposits or trades found for historical value calculation")
                return []

            # Create Polars DataFrame
            df = pl.DataFrame(combined_data)

            # Group by date and sum all changes for each day
            df = df.group_by("date").agg(pl.col("value").sum()).sort("date")

            # Get date range
            min_date = df["date"].min()
            max_date = date.today()

            self.logger.debug(f"Generating historical values from {min_date} to {max_date}")

            # Create a complete date range (all days)
            all_dates = pl.date_range(min_date, max_date, interval="1d", eager=True).to_frame("date")

            # Filter to weekdays only (Monday=1 to Friday=5)
            all_dates = all_dates.filter(pl.col("date").dt.weekday() <= 5)

            # Join with our data (left join to include all weekdays)
            result_df = all_dates.join(df, on="date", how="left")

            # Fill null values with 0 for days without changes
            result_df = result_df.with_columns(pl.col("value").fill_null(0))

            # Calculate cumulative sum
            result_df = result_df.with_columns(pl.col("value").cum_sum().alias("cumulative_value"))

            # Convert to list of DailyValue
            result = [
                DailyValue(x=row["date"].strftime("%Y-%m-%d"), y=row["cumulative_value"])
                for row in result_df.iter_rows(named=True)
            ]

            self.logger.debug(f"Generated {len(result)} historical data points")
            return result

        except Exception as e:
            self.logger.error(f"Failed to generate historical data: {e}")
            return []

    def calculate_product_growth(self) -> dict:
        """
        Calculate product growth over time.

        Metatrader4 doesn't provide sufficient historical data for growth calculations
        in the current implementation, so this returns an empty dictionary.

        Returns:
            dict: Empty dictionary (not supported by current MT4 implementation)
        """
        self.logger.debug("Product growth calculation not supported for MetaTrader 4")
        return {}
