"""Django ORM models for Alpaca Markets broker data."""

from django.db import models


class AlpacaPosition(models.Model):
    """Stores the current open positions for an Alpaca account."""

    class Meta:
        db_table = '"alpaca_position"'

    symbol = models.CharField(max_length=25, primary_key=True)
    qty = models.DecimalField(max_digits=20, decimal_places=10, default=0)
    avg_entry_price = models.DecimalField(max_digits=20, decimal_places=10, default=0, blank=True, null=True)
    market_value = models.DecimalField(max_digits=20, decimal_places=10, default=0, blank=True, null=True)
    current_price = models.DecimalField(max_digits=20, decimal_places=10, default=0, blank=True, null=True)
    unrealized_pl = models.DecimalField(max_digits=20, decimal_places=10, default=0, blank=True, null=True)
    cost_basis = models.DecimalField(max_digits=20, decimal_places=10, default=0, blank=True, null=True)
    side = models.CharField(max_length=10, default="long")
    currency = models.CharField(max_length=10, default="USD")
    synced_at = models.DateTimeField(auto_now=True)


class AlpacaOrder(models.Model):
    """Stores completed (filled) orders for an Alpaca account."""

    class Meta:
        db_table = '"alpaca_order"'

    order_id = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=25, db_index=True)
    qty = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    filled_qty = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    filled_avg_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    side = models.CharField(max_length=10)
    order_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    submitted_at = models.DateTimeField(blank=True, null=True)
    filled_at = models.DateTimeField(blank=True, null=True)


class AlpacaActivity(models.Model):
    """Stores account activities (dividends, deposits, withdrawals) for an Alpaca account."""

    class Meta:
        db_table = '"alpaca_activity"'

    activity_id = models.CharField(max_length=100, unique=True)
    activity_type = models.CharField(max_length=20, db_index=True)
    symbol = models.CharField(max_length=25, blank=True, null=True)
    qty = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    net_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    per_share_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    activity_date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
