from django.db import models

# Create your models here.

# This Model representes the CashMovements
# CashMovements are obtained from the AccountOverview or AccountReport DeGiro calls
class CashMovements(models.Model):
    # date,valueDate,id,description,currency,type,balance_unsettledCash,balance_flatexCash,balance_cashFund,balance_total,productId,change,exchangeRate,orderId
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
    
