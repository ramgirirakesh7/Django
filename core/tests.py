from __future__ import annotations
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import time, date
import json
from .models import Brand, Campaign, SpendLog
from .tasks import check_campaign_budgets, enforce_dayparting, reset_daily_spends, reset_monthly_spends


class BrandModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )

    def test_brand_creation(self) -> None:
        self.assertEqual(self.brand.name, "Test Brand")
        self.assertEqual(self.brand.daily_budget, Decimal('1000.00'))
        self.assertEqual(self.brand.monthly_budget, Decimal('30000.00'))
        self.assertEqual(str(self.brand), "Test Brand")

    def test_brand_campaign_relationship(self) -> None:
        campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )
        self.assertEqual(campaign.brand, self.brand)
        self.assertEqual(self.brand.campaigns.count(), 1)


class CampaignModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_campaign_creation(self) -> None:
        self.assertEqual(self.campaign.name, "Test Campaign")
        self.assertEqual(self.campaign.brand, self.brand)
        self.assertTrue(self.campaign.is_active)
        self.assertEqual(self.campaign.daily_spend, Decimal('0.00'))
        self.assertEqual(self.campaign.monthly_spend, Decimal('0.00'))
        self.assertEqual(self.campaign.dayparting_start, time(9, 0))
        self.assertEqual(self.campaign.dayparting_end, time(17, 0))

    def test_campaign_string_representation(self) -> None:
        self.assertEqual(str(self.campaign), "Test Campaign (Test Brand)")


class SpendLogModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_spend_log_creation(self) -> None:
        spend_log = SpendLog.objects.create(
            campaign=self.campaign,
            date=date.today(),
            amount=Decimal('100.00')
        )
        self.assertEqual(spend_log.campaign, self.campaign)
        self.assertEqual(spend_log.amount, Decimal('100.00'))
        self.assertEqual(spend_log.date, date.today())

    def test_spend_log_string_representation(self) -> None:
        spend_log = SpendLog.objects.create(
            campaign=self.campaign,
            date=date.today(),
            amount=Decimal('100.00')
        )
        expected = f"Test Campaign - {date.today()}: 100.00"
        self.assertEqual(str(spend_log), expected)


class APITest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_brand_list_api(self) -> None:
        response = self.client.get('/api/brands/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['brands']), 1)
        self.assertEqual(data['brands'][0]['name'], "Test Brand")

    def test_create_brand_api(self) -> None:
        data = {
            'name': 'New Brand',
            'daily_budget': '500.00',
            'monthly_budget': '15000.00'
        }
        response = self.client.post(
            '/api/brands/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'New Brand')
        self.assertEqual(Brand.objects.count(), 2)

    def test_campaign_list_api(self) -> None:
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['campaigns']), 1)
        self.assertEqual(data['campaigns'][0]['name'], "Test Campaign")

    def test_create_campaign_api(self) -> None:
        data = {
            'name': 'New Campaign',
            'brand_id': self.brand.id,
            'dayparting_start': '10:00',
            'dayparting_end': '18:00'
        }
        response = self.client.post(
            '/api/campaigns/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'New Campaign')
        self.assertEqual(Campaign.objects.count(), 2)

    def test_add_spend_api(self) -> None:
        data = {
            'campaign_id': self.campaign.id,
            'amount': '100.00'
        }
        response = self.client.post(
            '/api/spend/add/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['amount'], '100.00')
        
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.daily_spend, Decimal('100.00'))
        self.assertEqual(self.campaign.monthly_spend, Decimal('100.00'))
        
        self.assertEqual(SpendLog.objects.count(), 1)

    def test_add_spend_exceeds_budget(self) -> None:
        data = {
            'campaign_id': self.campaign.id,
            'amount': '1500.00'
        }
        response = self.client.post(
            '/api/spend/add/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('exceed budget', response_data['error'])

    def test_spend_logs_api(self) -> None:
        SpendLog.objects.create(
            campaign=self.campaign,
            date=date.today(),
            amount=Decimal('100.00')
        )
        
        response = self.client.get('/api/spend/logs/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['spend_logs']), 1)
        self.assertEqual(data['spend_logs'][0]['amount'], '100.00')

    def test_system_status_api(self) -> None:
        response = self.client.get('/api/status/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['total_brands'], 1)
        self.assertEqual(data['total_campaigns'], 1)
        self.assertEqual(data['active_campaigns'], 1)


class CeleryTasksTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_check_campaign_budgets(self) -> None:
        self.campaign.daily_spend = Decimal('1100.00')
        self.campaign.save()
        
        check_campaign_budgets()
        
        self.campaign.refresh_from_db()
        self.assertFalse(self.campaign.is_active)

    def test_enforce_dayparting(self) -> None:
        self.campaign.dayparting_start = time(10, 0)
        self.campaign.dayparting_end = time(16, 0)
        self.campaign.save()
        
        enforce_dayparting()
        
        self.campaign.refresh_from_db()

    def test_reset_daily_spends(self) -> None:
        self.campaign.daily_spend = Decimal('500.00')
        self.campaign.save()
        
        reset_daily_spends()
        
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.daily_spend, Decimal('0.00'))

    def test_reset_monthly_spends(self) -> None:
        self.campaign.monthly_spend = Decimal('5000.00')
        self.campaign.save()
        
        reset_monthly_spends()
        
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.monthly_spend, Decimal('0.00'))


class ManagementCommandTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal('1000.00'),
            monthly_budget=Decimal('30000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_simulate_spend_command(self) -> None:
        from django.core.management import call_command
        from django.test.utils import captured_stdout
        
        initial_daily_spend = self.campaign.daily_spend
        initial_monthly_spend = self.campaign.monthly_spend
        initial_spend_logs = SpendLog.objects.count()
        
        with captured_stdout() as stdout:
            call_command('simulate_spend')
        
        self.campaign.refresh_from_db()
        self.assertGreater(self.campaign.daily_spend, initial_daily_spend)
        self.assertGreater(self.campaign.monthly_spend, initial_monthly_spend)
        
        self.assertGreater(SpendLog.objects.count(), initial_spend_logs)
        
        output = stdout.getvalue()
        self.assertIn("Added spend", output)


class IntegrationTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.brand = Brand.objects.create(
            name="Integration Brand",
            daily_budget=Decimal('500.00'),
            monthly_budget=Decimal('5000.00')
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Integration Campaign",
            dayparting_start=time(9, 0),
            dayparting_end=time(17, 0)
        )

    def test_full_spend_workflow(self) -> None:
        data = {'campaign_id': self.campaign.id, 'amount': '200.00'}
        response = self.client.post(
            '/api/spend/add/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = {'campaign_id': self.campaign.id, 'amount': '300.00'}
        response = self.client.post(
            '/api/spend/add/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.daily_spend, Decimal('500.00'))
        self.assertFalse(self.campaign.is_active)
        
        data = {'campaign_id': self.campaign.id, 'amount': '100.00'}
        response = self.client.post(
            '/api/spend/add/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('not active', response_data['error'])
        
        reset_daily_spends()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.daily_spend, Decimal('0.00'))
        self.assertTrue(self.campaign.is_active) 