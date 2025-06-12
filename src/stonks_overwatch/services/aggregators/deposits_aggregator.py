from datetime import date
from typing import List

import pandas as pd

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.services.models import Deposit, PortfolioId
from stonks_overwatch.utils.core.localization import LocalizationUtility

class DepositsAggregatorService(BaseAggregator):

    def __init__(self):
        super().__init__(ServiceType.DEPOSIT)

    def cash_deposits_history(self, selected_portfolio: PortfolioId) -> list[dict]:
        cash_contributions = self.get_cash_deposits(selected_portfolio)
        df = pd.DataFrame.from_dict(cash_contributions)

        # Group by day, adding the values
        df.set_index("datetime", inplace=True)
        df = df.sort_values(by="datetime")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cumulative sum
        df["contributed"] = df["change"].cumsum()

        cash_contributions = df.to_dict("records")
        for contribution in cash_contributions:
            contribution["datetime"] = contribution["datetime"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["datetime"],
                    "total_deposit": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "date": LocalizationUtility.format_date_from_date(date.today()),
                "total_deposit": cash_contributions[-1]["contributed"],
            }
        )

        return dataset

    def get_cash_deposits(self, selected_portfolio: PortfolioId) -> List[Deposit]:
        # Use the new helper method to collect and sort deposit data
        return self._collect_and_sort(
            selected_portfolio,
            "get_cash_deposits",
            sort_key=lambda x: x.datetime,
            reverse=True
        )

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> List[Deposit]:
        """
        Aggregate deposit data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_cash_deposits(selected_portfolio)
