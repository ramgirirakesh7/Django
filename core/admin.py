from django.contrib import admin
from .models import Brand, Campaign, SpendLog

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "daily_budget", "monthly_budget")

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "brand", "is_active", "daily_spend", "monthly_spend", "dayparting_start", "dayparting_end")
    list_filter = ("brand", "is_active")

@admin.register(SpendLog)
class SpendLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("campaign", "date", "amount")
    list_filter = ("campaign", "date") 