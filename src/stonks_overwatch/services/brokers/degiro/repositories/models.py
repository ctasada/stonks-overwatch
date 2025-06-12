from django.db import models

# Create your models here.


# This Model represents the CashMovements
# CashMovements are obtained from the AccountOverview or AccountReport DeGiro calls
class DeGiroCashMovements(models.Model):
    class Meta:
        db_table = '"degiro_cashmovements"'

    date = models.DateTimeField()
    value_date = models.DateTimeField()
    description = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    type = models.CharField(max_length=200)
    balance_unsettled_cash = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_flatex_cash = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_cash_fund = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_total = models.CharField(max_length=200, default=None, blank=True, null=True)
    product_id = models.CharField(max_length=20, default=None, blank=True, null=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    order_id = models.CharField(max_length=200, default=None, blank=True, null=True)


class DeGiroTransactions(models.Model):
    class Meta:
        db_table = '"degiro_transactions"'

    id = models.PositiveIntegerField(primary_key=True)
    product_id = models.PositiveIntegerField()
    date = models.DateTimeField()
    buysell = models.CharField(max_length=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    order_type_id = models.PositiveIntegerField(default=None, blank=True, null=True)
    counter_party = models.CharField(max_length=5, default=None, blank=True, null=True)
    transfered = models.BooleanField()
    fx_rate = models.DecimalField(max_digits=10, decimal_places=4)
    nett_fx_rate = models.DecimalField(max_digits=10, decimal_places=4)
    gross_fx_rate = models.DecimalField(max_digits=10, decimal_places=4)
    auto_fx_fee_in_base_currency = models.DecimalField(max_digits=15, decimal_places=10)
    total_in_base_currency = models.DecimalField(max_digits=15, decimal_places=10)
    fee_in_base_currency = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    total_fees_in_base_currency = models.DecimalField(max_digits=15, decimal_places=10)
    total_plus_fee_in_base_currency = models.DecimalField(max_digits=15, decimal_places=10)
    total_plus_all_fees_in_base_currency = models.DecimalField(max_digits=15, decimal_places=10)
    transaction_type_id = models.PositiveIntegerField()
    trading_venue = models.CharField(max_length=5, default=None, blank=True, null=True)
    executing_entity_id = models.CharField(max_length=30, default=None, blank=True, null=True)


class DeGiroProductInfo(models.Model):
    class Meta:
        db_table = '"degiro_productinfo"'

    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    isin = models.CharField(max_length=25)
    symbol = models.CharField(max_length=8)
    contract_size = models.DecimalField(max_digits=10, decimal_places=1)
    product_type = models.CharField(max_length=25)
    product_type_id = models.PositiveIntegerField()
    tradable = models.BooleanField()
    category = models.CharField(max_length=1)
    currency = models.CharField(max_length=3)
    active = models.BooleanField()
    exchange_id = models.CharField(max_length=4)
    only_eod_prices = models.BooleanField()
    is_shortable = models.BooleanField(default=None, blank=True, null=True)
    feed_quality = models.CharField(max_length=2, default=None, blank=True, null=True)
    order_book_depth = models.PositiveIntegerField(default=None, blank=True, null=True)
    vwd_identifier_type = models.CharField(max_length=16, default=None, blank=True, null=True)
    vwd_id = models.CharField(max_length=32, default=None, blank=True, null=True)
    quality_switchable = models.BooleanField(default=None, blank=True, null=True)
    quality_switch_free = models.BooleanField(default=None, blank=True, null=True)
    vwd_module_id = models.PositiveIntegerField(default=None, blank=True, null=True)
    feed_quality_secondary = models.CharField(max_length=8, default=None, blank=True, null=True)
    order_book_depth_secondary = models.PositiveIntegerField(default=None, blank=True, null=True)
    vwd_identifier_type_secondary = models.CharField(max_length=8, default=None, blank=True, null=True)
    vwd_id_secondary = models.CharField(max_length=16, default=None, blank=True, null=True)
    quality_switchable_secondary = models.BooleanField(default=None, blank=True, null=True)
    quality_switch_free_secondary = models.BooleanField(default=None, blank=True, null=True)
    vwd_module_id_secondary = models.PositiveIntegerField(default=None, blank=True, null=True)


class DeGiroProductQuotation(models.Model):
    class Meta:
        db_table = '"degiro_productquotation"'

    id = models.PositiveIntegerField(primary_key=True)
    interval = models.CharField(max_length=10)
    last_import = models.DateTimeField()
    quotations = models.JSONField()


class DeGiroCompanyProfile(models.Model):
    class Meta:
        db_table = '"degiro_companyprofile"'

    isin = models.CharField(max_length=25, primary_key=True)
    data = models.JSONField()

class DeGiroUpcomingPayments(models.Model):
    class Meta:
        db_table = '"degiro_upcomingpayments"'

    id = models.AutoField(primary_key=True)
    ca_id = models.CharField(max_length=20)
    product = models.CharField(max_length=200)
    description = models.CharField(max_length=255)
    currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_in_base_curr = models.DecimalField(max_digits=12, decimal_places=2)
    pay_date = models.DateField()

class DeGiroAgendaDividend(models.Model):
    class Meta:
        db_table = '"degiro_agendadividend"'

    event_id = models.BigIntegerField(primary_key=True)
    isin = models.CharField(max_length=25)
    ric = models.CharField(max_length=16)
    organization_name = models.CharField(max_length=200)
    date_time = models.DateTimeField()
    last_update = models.DateTimeField()
    country_code = models.CharField(max_length=4)
    event_type = models.CharField(max_length=32)
    ex_dividend_date = models.DateTimeField()
    payment_date = models.DateTimeField()
    dividend = models.DecimalField(max_digits=10, decimal_places=4)
    yield_value = models.DecimalField(max_digits=10, decimal_places=4)
    currency = models.CharField(max_length=3)
    market_cap = models.CharField(max_length=16)
