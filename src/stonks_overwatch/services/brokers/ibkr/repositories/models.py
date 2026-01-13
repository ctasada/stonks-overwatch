from django.db import models


# Create your models here.
class IBKRPosition(models.Model):
    class Meta:
        db_table = '"ibkr_positions"'

    conid = models.PositiveIntegerField(primary_key=True)
    acct_id = models.CharField(max_length=20)
    contract_desc = models.CharField(max_length=8)
    position = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    mkt_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    mkt_value = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    currency = models.CharField(max_length=3)
    avg_cost = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    avg_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_mkt_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_mkt_value = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_avg_cost = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_avg_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_realized_pnl = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    base_unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    asset_class = models.CharField(max_length=20, null=True, blank=True)
    listing_exchange = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    group = models.CharField(max_length=200, default=None, null=True)
    sector = models.CharField(max_length=200, default=None, null=True)
    sector_group = models.CharField(max_length=200, default=None, null=True)
    ticker = models.CharField(max_length=25, null=True, blank=True)
    type = models.CharField(max_length=25, null=True, blank=True)
    full_name = models.CharField(max_length=25, null=True, blank=True)
    is_us = models.BooleanField(null=True, blank=True, default=None)


class IBKRTransactions(models.Model):
    class Meta:
        db_table = '"ibkr_transactions"'
        constraints = [models.UniqueConstraint(fields=["date", "acct_id", "conid"], name="unique_transaction")]

    id = models.CharField(primary_key=True, max_length=20)
    acct_id = models.CharField(max_length=20)
    conid = models.PositiveIntegerField()
    date = models.DateTimeField()
    cur = models.CharField(max_length=3)
    fx_rate = models.DecimalField(max_digits=20, decimal_places=10, default=None, null=True)
    pr = models.DecimalField(max_digits=20, decimal_places=10, default=None, null=True)
    qty = models.DecimalField(max_digits=20, decimal_places=10, default=None, null=True)
    amt = models.DecimalField(max_digits=20, decimal_places=10)
    type = models.CharField(max_length=200)
    desc = models.CharField(max_length=200)
