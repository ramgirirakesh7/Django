from __future__ import annotations
from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import date, time
from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import Manager

class Brand(models.Model):
    name = models.CharField(max_length=100)
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_budget = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self) -> str:
        return self.name

class Campaign(models.Model):
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    daily_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_spend = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    dayparting_start = models.TimeField()
    dayparting_end = models.TimeField()

    def __str__(self) -> str:
        return f"{self.name} ({self.brand.name})"

class SpendLog(models.Model):
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name="spend_logs")
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.date}: {self.amount}" 