from __future__ import annotations
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from core.models import Campaign, SpendLog
import random
from typing import Any

class Command(BaseCommand):
    help = 'Simulate ad spend events for campaigns.'

    def handle(self, *args: Any, **options: Any) -> None:
        for campaign in Campaign.objects.all():
            if campaign.is_active:
                amount = Decimal(random.randint(1, 100))
                campaign.daily_spend += amount
                campaign.monthly_spend += amount
                campaign.save(update_fields=["daily_spend", "monthly_spend"])
                SpendLog.objects.create(
                    campaign=campaign,
                    date=timezone.localdate(),
                    amount=amount
                )
                self.stdout.write(self.style.SUCCESS(f"Added spend {amount} to {campaign.name}")) 