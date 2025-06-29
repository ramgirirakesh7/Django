from __future__ import annotations
from celery import shared_task
from django.utils import timezone
from decimal import Decimal
from datetime import time
from .models import Campaign, Brand
from typing import Any

@shared_task  # type: ignore
def check_campaign_budgets() -> None:
    for campaign in Campaign.objects.select_related('brand').all():
        if (campaign.daily_spend >= campaign.brand.daily_budget or
            campaign.monthly_spend >= campaign.brand.monthly_budget):
            if campaign.is_active:
                campaign.is_active = False
                campaign.save(update_fields=["is_active"])

@shared_task  # type: ignore
def enforce_dayparting() -> None:
    now: time = timezone.localtime().time()
    for campaign in Campaign.objects.select_related('brand').all():
        in_window = campaign.dayparting_start <= now <= campaign.dayparting_end
        within_budget = (
            campaign.daily_spend < campaign.brand.daily_budget and
            campaign.monthly_spend < campaign.brand.monthly_budget
        )
        if in_window and within_budget:
            if not campaign.is_active:
                campaign.is_active = True
                campaign.save(update_fields=["is_active"])
        else:
            if campaign.is_active:
                campaign.is_active = False
                campaign.save(update_fields=["is_active"])

@shared_task  # type: ignore
def reset_daily_spends() -> None:
    for campaign in Campaign.objects.select_related('brand').all():
        campaign.daily_spend = Decimal('0.00')
        if (campaign.monthly_spend < campaign.brand.monthly_budget):
            campaign.is_active = True
        campaign.save(update_fields=["daily_spend", "is_active"])

@shared_task  # type: ignore
def reset_monthly_spends() -> None:
    for campaign in Campaign.objects.select_related('brand').all():
        campaign.monthly_spend = Decimal('0.00')
        campaign.is_active = True
        campaign.save(update_fields=["monthly_spend", "is_active"]) 