from django.db import models


# Full Yahoo Finance Ticker Information
class YFinanceTickerInfo(models.Model):
    class Meta:
        db_table = '"yfinance_ticker_info"'

    symbol = models.CharField(max_length=8)
    data = models.JSONField()


# This Model represents the Yahoo Finance Stock Splits
# The data field contains the result of the yfinance.Ticker.splits.to_dict() method
class YFinanceStockSplits(models.Model):
    class Meta:
        db_table = '"yfinance_stock_splits"'

    symbol = models.CharField(max_length=8)
    data = models.JSONField()
