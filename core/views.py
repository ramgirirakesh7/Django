from __future__ import annotations
from typing import Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction, models
from decimal import Decimal
import json
from .models import Brand, Campaign, SpendLog
from django.utils import timezone


@csrf_exempt
@require_http_methods(["GET"])
def brand_list(request) -> JsonResponse:
    brands = Brand.objects.all()
    data = []
    for brand in brands:
        data.append({
            'id': brand.id,
            'name': brand.name,
            'daily_budget': str(brand.daily_budget),
            'monthly_budget': str(brand.monthly_budget),
            'campaigns_count': brand.campaigns.count()
        })
    return JsonResponse({'brands': data})


@csrf_exempt
@require_http_methods(["POST"])
def create_brand(request) -> JsonResponse:
    try:
        data = json.loads(request.body)
        name = data.get('name')
        daily_budget = Decimal(data.get('daily_budget', '0'))
        monthly_budget = Decimal(data.get('monthly_budget', '0'))
        
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        
        brand = Brand.objects.create(
            name=name,
            daily_budget=daily_budget,
            monthly_budget=monthly_budget
        )
        
        return JsonResponse({
            'id': brand.id,
            'name': brand.name,
            'daily_budget': str(brand.daily_budget),
            'monthly_budget': str(brand.monthly_budget)
        }, status=201)
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def campaign_list(request) -> JsonResponse:
    campaigns = Campaign.objects.select_related('brand').all()
    data = []
    for campaign in campaigns:
        data.append({
            'id': campaign.id,
            'name': campaign.name,
            'brand': campaign.brand.name,
            'brand_id': campaign.brand.id,
            'is_active': campaign.is_active,
            'daily_spend': str(campaign.daily_spend),
            'monthly_spend': str(campaign.monthly_spend),
            'dayparting_start': campaign.dayparting_start.strftime('%H:%M'),
            'dayparting_end': campaign.dayparting_end.strftime('%H:%M'),
            'daily_budget': str(campaign.brand.daily_budget),
            'monthly_budget': str(campaign.brand.monthly_budget)
        })
    return JsonResponse({'campaigns': data})


@csrf_exempt
@require_http_methods(["POST"])
def create_campaign(request) -> JsonResponse:
    try:
        data = json.loads(request.body)
        name = data.get('name')
        brand_id = data.get('brand_id')
        dayparting_start = data.get('dayparting_start', '09:00')
        dayparting_end = data.get('dayparting_end', '17:00')
        
        if not name or not brand_id:
            return JsonResponse({'error': 'Name and brand_id are required'}, status=400)
        
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return JsonResponse({'error': 'Brand not found'}, status=404)
        
        from datetime import time
        start_time = time.fromisoformat(dayparting_start)
        end_time = time.fromisoformat(dayparting_end)
        
        campaign = Campaign.objects.create(
            name=name,
            brand=brand,
            dayparting_start=start_time,
            dayparting_end=end_time
        )
        
        return JsonResponse({
            'id': campaign.id,
            'name': campaign.name,
            'brand': campaign.brand.name,
            'is_active': campaign.is_active,
            'dayparting_start': campaign.dayparting_start.strftime('%H:%M'),
            'dayparting_end': campaign.dayparting_end.strftime('%H:%M')
        }, status=201)
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def add_spend(request) -> JsonResponse:
    try:
        data = json.loads(request.body)
        campaign_id = data.get('campaign_id')
        amount = Decimal(data.get('amount', '0'))
        
        if not campaign_id or amount <= 0:
            return JsonResponse({'error': 'Valid campaign_id and amount are required'}, status=400)
        
        try:
            campaign = Campaign.objects.select_related('brand').get(id=campaign_id)
        except Campaign.DoesNotExist:
            return JsonResponse({'error': 'Campaign not found'}, status=404)
        
        with transaction.atomic():
            if not campaign.is_active:
                return JsonResponse({'error': 'Campaign is not active'}, status=400)
            
            if (campaign.daily_spend + amount > campaign.brand.daily_budget or
                campaign.monthly_spend + amount > campaign.brand.monthly_budget):
                return JsonResponse({'error': 'Spend would exceed budget limits'}, status=400)
            
            campaign.daily_spend += amount
            campaign.monthly_spend += amount
            campaign.save(update_fields=['daily_spend', 'monthly_spend'])
            
            SpendLog.objects.create(
                campaign=campaign,
                date=timezone.localdate(),
                amount=amount
            )
            
            if (campaign.daily_spend >= campaign.brand.daily_budget or
                campaign.monthly_spend >= campaign.brand.monthly_budget):
                campaign.is_active = False
                campaign.save(update_fields=['is_active'])
        
        return JsonResponse({
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'amount': str(amount),
            'new_daily_spend': str(campaign.daily_spend),
            'new_monthly_spend': str(campaign.monthly_spend),
            'is_active': campaign.is_active
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def spend_logs(request) -> JsonResponse:
    campaign_id = request.GET.get('campaign_id')
    date = request.GET.get('date')
    
    logs = SpendLog.objects.select_related('campaign', 'campaign__brand')
    
    if campaign_id:
        logs = logs.filter(campaign_id=campaign_id)
    
    if date:
        logs = logs.filter(date=date)
    
    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'campaign_name': log.campaign.name,
            'brand_name': log.campaign.brand.name,
            'date': log.date.isoformat(),
            'amount': str(log.amount)
        })
    
    return JsonResponse({'spend_logs': data})


@csrf_exempt
@require_http_methods(["GET"])
def system_status(request) -> JsonResponse:
    total_brands = Brand.objects.count()
    total_campaigns = Campaign.objects.count()
    active_campaigns = Campaign.objects.filter(is_active=True).count()
    paused_campaigns = total_campaigns - active_campaigns
    
    over_daily_budget = Campaign.objects.filter(
        daily_spend__gte=models.F('brand__daily_budget')
    ).count()
    
    over_monthly_budget = Campaign.objects.filter(
        monthly_spend__gte=models.F('brand__monthly_budget')
    ).count()
    
    return JsonResponse({
        'total_brands': total_brands,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'paused_campaigns': paused_campaigns,
        'over_daily_budget': over_daily_budget,
        'over_monthly_budget': over_monthly_budget,
        'server_time': timezone.now().isoformat()
    }) 