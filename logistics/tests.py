from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, CompanyProfile, CarrierProfile
from .models import Route, Bid, Tracking

User = get_user_model()


class RouteModelTest(TestCase):
    def setUp(self):
        self.company = User.objects.create_user(
            username='company',
            password='testpass',
            email='company@test.com',
            role='company',
            company_name='Test Company'
        )
        CompanyProfile.objects.create(
            user=self.company,
            address='Test Address',
            tax_id='12345678'
        )
        
        self.carrier = User.objects.create_user(
            username='carrier',
            password='testpass',
            email='carrier@test.com',
            role='carrier'
        )
        CarrierProfile.objects.create(
            user=self.carrier,
            license_number='LIC123',
            vehicle_type='Вантажівка'
        )
    
    def test_create_route(self):
        route = Route.objects.create(
            company=self.company,
            origin_city='Київ',
            origin_country='Україна',
            origin_lat=50.4501,
            origin_lng=30.5234,
            destination_city='Львів',
            destination_country='Україна',
            destination_lat=49.8397,
            destination_lng=24.0297,
            cargo_type='Пакування',
            weight=100.00,
            volume=5.00,
            price=5000.00,
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=3),
            status='pending'
        )
        self.assertEqual(route.company, self.company)
        self.assertEqual(route.status, 'pending')
        self.assertEqual(route.origin_city, 'Київ')
    
    def test_create_bid(self):
        route = Route.objects.create(
            company=self.company,
            origin_city='Київ',
            origin_country='Україна',
            origin_lat=50.4501,
            origin_lng=30.5234,
            destination_city='Львів',
            destination_country='Україна',
            destination_lat=49.8397,
            destination_lng=24.0297,
            cargo_type='Пакування',
            weight=100.00,
            volume=5.00,
            price=5000.00,
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=3),
            status='pending'
        )
        
        bid = Bid.objects.create(
            route=route,
            carrier=self.carrier,
            proposed_price=4500.00,
            estimated_delivery=timezone.now() + timedelta(days=3)
        )
        
        self.assertEqual(bid.route, route)
        self.assertEqual(bid.carrier, self.carrier)
        self.assertFalse(bid.is_accepted)
    
    def test_route_string_representation(self):
        route = Route.objects.create(
            company=self.company,
            origin_city='Київ',
            origin_country='Україна',
            origin_lat=50.4501,
            origin_lng=30.5234,
            destination_city='Львів',
            destination_country='Україна',
            destination_lat=49.8397,
            destination_lng=24.0297,
            cargo_type='Пакування',
            weight=100.00,
            volume=5.00,
            price=5000.00,
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=3),
            status='pending'
        )
        self.assertIn('Київ', str(route))
        self.assertIn('Львів', str(route))


class RouteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = User.objects.create_user(
            username='company',
            password='testpass',
            email='company@test.com',
            role='company',
            company_name='Test Company'
        )
        CompanyProfile.objects.create(
            user=self.company,
            address='Test Address',
            tax_id='12345678'
        )
        
        self.carrier = User.objects.create_user(
            username='carrier',
            password='testpass',
            email='carrier@test.com',
            role='carrier'
        )
        
        self.route = Route.objects.create(
            company=self.company,
            origin_city='Київ',
            origin_country='Україна',
            origin_lat=50.4501,
            origin_lng=30.5234,
            destination_city='Львів',
            destination_country='Україна',
            destination_lat=49.8397,
            destination_lng=24.0297,
            cargo_type='Пакування',
            weight=100.00,
            volume=5.00,
            price=5000.00,
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=3),
            status='pending'
        )
        Tracking.objects.create(route=self.route)
    
    def test_routes_list_requires_login(self):
        response = self.client.get(reverse('routes_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_routes_list_for_company(self):
        self.client.login(username='company', password='testpass')
        response = self.client.get(reverse('routes_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_route_requires_company(self):
        self.client.login(username='carrier', password='testpass')
        response = self.client.get(reverse('create_route'))
        self.assertEqual(response.status_code, 302)  # Redirect (only companies can create)
    
    def test_route_detail_view(self):
        self.client.login(username='company', password='testpass')
        response = self.client.get(reverse('route_detail', args=[self.route.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Київ', response.content.decode())


class BidViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = User.objects.create_user(
            username='company',
            password='testpass',
            email='company@test.com',
            role='company',
            company_name='Test Company'
        )
        CompanyProfile.objects.create(
            user=self.company,
            address='Test Address',
            tax_id='12345678'
        )
        
        self.carrier = User.objects.create_user(
            username='carrier',
            password='testpass',
            email='carrier@test.com',
            role='carrier'
        )
        CarrierProfile.objects.create(
            user=self.carrier,
            license_number='LIC123',
            vehicle_type='Вантажівка'
        )
        
        self.route = Route.objects.create(
            company=self.company,
            origin_city='Київ',
            origin_country='Україна',
            origin_lat=50.4501,
            origin_lng=30.5234,
            destination_city='Львів',
            destination_country='Україна',
            destination_lat=49.8397,
            destination_lng=24.0297,
            cargo_type='Пакування',
            weight=100.00,
            volume=5.00,
            price=5000.00,
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=3),
            status='pending'
        )
    
    def test_create_bid_requires_carrier(self):
        self.client.login(username='company', password='testpass')
        response = self.client.get(reverse('create_bid', args=[self.route.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect (only carriers can bid)
    
    def test_accept_bid_requires_company(self):
        bid = Bid.objects.create(
            route=self.route,
            carrier=self.carrier,
            proposed_price=4500.00,
            estimated_delivery=timezone.now() + timedelta(days=3)
        )
        
        self.client.login(username='carrier', password='testpass')
        response = self.client.get(reverse('accept_bid', args=[bid.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect (only companies can accept)
