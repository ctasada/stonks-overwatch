from django.db import models

# Create your models here.

# This Model representes the CashMovements
# CashMovements are obtained from the AccountOverview or AccountReport DeGiro calls
class CashMovements(models.Model):
    date = models.DateTimeField()
    valueDate = models.DateTimeField()
    description = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    change = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=200)
