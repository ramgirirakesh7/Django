"""budget_manager URL Configuration"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/brands/', views.brand_list, name='brand_list'),
    path('api/brands/create/', views.create_brand, name='create_brand'),
    path('api/campaigns/', views.campaign_list, name='campaign_list'),
    path('api/campaigns/create/', views.create_campaign, name='create_campaign'),
    path('api/spend/add/', views.add_spend, name='add_spend'),
    path('api/spend/logs/', views.spend_logs, name='spend_logs'),
    path('api/status/', views.system_status, name='system_status'),
] 