from datetime import timezone as dt_timezone
from typing import List

import polars as pl
from django.utils import timezone

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import Deposit, PortfolioId
from stonks_overwatch.utils.core.localization import LocalizationUtility


class DepositsAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.DEPOSIT)

    def cash_deposits_history(self, selected_portfolio: PortfolioId) -> list[dict]:
        cash_contributions = self.get_cash_deposits(selected_portfolio)

        # Convert list of Deposit objects to polars DataFrame
        # Extract the data we need from Deposit objects
        # Normalize all datetimes to UTC to avoid timezone mismatch in Polars
        deposit_data = []
        for deposit in cash_contributions:
            # Convert to UTC to ensure consistent timezone across all deposits
            dt_utc = deposit.datetime.astimezone(dt_timezone.utc) if deposit.datetime.tzinfo else deposit.datetime
            deposit_data.append({"datetime": dt_utc, "change": deposit.change})

        if not deposit_data:
            return []

        df = pl.DataFrame(deposit_data)

        # Convert datetime to date for grouping and sort by datetime
        df = df.with_columns(pl.col("datetime").dt.date().alias("date"))
        df = df.sort("datetime")

        # Group by date, summing the changes
        df = df.group_by("date").agg(pl.col("change").sum())
        df = df.sort("date")

        # Calculate cumulative sum
        df = df.with_columns(pl.col("change").cum_sum().alias("contributed"))

        # Convert to list of dictionaries and format dates
        cash_contributions = df.to_dicts()
        for contribution in cash_contributions:
            contribution["datetime"] = contribution["date"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["datetime"],
                    "total_deposit": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        if cash_contributions:
            dataset.append(
                {
                    "date": LocalizationUtility.format_date_from_date(timezone.now().date()),
                    "total_deposit": cash_contributions[-1]["contributed"],
                }
            )

        return dataset

    def get_cash_deposits(self, selected_portfolio: PortfolioId) -> List[Deposit]:
        # Use the new helper method to collect and sort deposit data
        return self._collect_and_sort(
            selected_portfolio, "get_cash_deposits", sort_key=lambda x: x.datetime, reverse=True
        )

    def aggregate_data(self, selected_portfolio: PortfolioId) -> List[Deposit]:
        """
        Aggregate deposit data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_cash_deposits(selected_portfolio)
