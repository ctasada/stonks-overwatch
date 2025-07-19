from django.db import models


class BitvavoBalance(models.Model):
    class Meta:
        db_table = '"bitvavo_balance"'

    symbol = models.CharField(max_length=25, primary_key=True)
    available = models.DecimalField(max_digits=20, decimal_places=10, default=0.0)


class BitvavoTransactions(models.Model):
    class Meta:
        db_table = '"bitvavo_transactions"'

    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=50, unique=True)
    executed_at = models.DateTimeField()
    type = models.CharField(max_length=20)
    price_currency = models.CharField(max_length=10, default=None, blank=True, null=True)
    price_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    sent_currency = models.CharField(max_length=10, default=None, blank=True, null=True)
    sent_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    received_currency = models.CharField(max_length=10, default=None, blank=True, null=True)
    received_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    fees_currency = models.CharField(max_length=10, default=None, blank=True, null=True)
    fees_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    address = models.CharField(max_length=100, default=None, blank=True, null=True)


class BitvavoProductQuotation(models.Model):
    class Meta:
        db_table = '"bitvavo_productquotation"'

    symbol = models.CharField(max_length=25, primary_key=True)
    interval = models.CharField(max_length=10)
    last_import = models.DateTimeField()
    quotations = models.JSONField()


class BitvavoAssets(models.Model):
    class Meta:
        db_table = '"bitvavo_assets"'

    symbol = models.CharField(max_length=25, primary_key=True)
    name = models.CharField(max_length=100, default=None, blank=True, null=True)
    decimals = models.IntegerField(default=0)
    deposit_fee = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    deposit_confirmations = models.IntegerField(default=0)
    deposit_status = models.CharField(max_length=20)
    withdrawal_fee = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    withdrawal_min_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    withdrawal_status = models.CharField(max_length=20)
    networks = models.JSONField(default=list, blank=True, null=True)
    message = models.CharField(max_length=255, default=None, blank=True, null=True)


class BitvavoDepositHistory(models.Model):
    class Meta:
        db_table = '"bitvavo_deposit_history"'

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    symbol = models.CharField(max_length=25)
    amount = models.DecimalField(max_digits=20, decimal_places=10)
    address = models.CharField(max_length=100, default=None, blank=True, null=True)
    payment_id = models.CharField(max_length=50, unique=True, default=None, blank=True, null=True)
    tx_id = models.CharField(max_length=50, unique=True, default=None, blank=True, null=True)
    fee = models.DecimalField(max_digits=20, decimal_places=10)
    status = models.CharField(max_length=20)
