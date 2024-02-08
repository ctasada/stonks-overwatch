from django.db import models

# Create your models here.

# This Model representes the CashMovements
# CashMovements are obtained from the AccountOverview or AccountReport DeGiro calls
class CashMovements(models.Model):
    date = models.DateTimeField()
    valueDate = models.DateTimeField()
    description = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    type = models.CharField(max_length=200)
    balance_unsettledCash = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_flatexCash = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_cashFund = models.CharField(max_length=200, default=None, blank=True, null=True)
    balance_total = models.CharField(max_length=200, default=None, blank=True, null=True)
    productId = models.CharField(max_length=20, default=None, blank=True, null=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    exchangeRate = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    orderId = models.CharField(max_length=200, default=None, blank=True, null=True)
    
class Transactions(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    productId = models.PositiveIntegerField()
    date = models.DateTimeField()
    buysell = models.CharField(max_length=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    orderTypeId = models.PositiveIntegerField(default=None, blank=True, null=True)
    counterParty = models.CharField(max_length=5, default=None, blank=True, null=True)
    transfered = models.BooleanField()
    fxRate = models.DecimalField(max_digits=10, decimal_places=4)
    nettFxRate = models.DecimalField(max_digits=10, decimal_places=4)
    grossFxRate = models.DecimalField(max_digits=10, decimal_places=4)
    autoFxFeeInBaseCurrency = models.DecimalField(max_digits=15, decimal_places=10)
    totalInBaseCurrency = models.DecimalField(max_digits=15, decimal_places=10)
    feeInBaseCurrency = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    totalFeesInBaseCurrency = models.DecimalField(max_digits=15, decimal_places=10)
    totalPlusFeeInBaseCurrency = models.DecimalField(max_digits=15, decimal_places=10)
    totalPlusAllFeesInBaseCurrency = models.DecimalField(max_digits=15, decimal_places=10)
    transactionTypeId = models.PositiveIntegerField()
    tradingVenue = models.CharField(max_length=5, default=None, blank=True, null=True)
    executingEntityId = models.CharField(max_length=30, default=None, blank=True, null=True)
