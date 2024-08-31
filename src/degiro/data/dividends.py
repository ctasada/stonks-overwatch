from degiro.data.account_overview import AccountOverviewData


class DividendsData:
    def __init__(self):
        self.account_overview = AccountOverviewData()

    def get_dividends(self):
        overview = self.account_overview.get_account_overview()

        dividends = []
        for transaction in overview:
            # We don't include 'Dividendbelasting' because the 'value' seems to already include the taxes
            if transaction["description"] in [
                "Dividend",
                "Dividendbelasting",
                "Vermogenswinst",
            ]:
                dividends.append(transaction)

        return dividends
