from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import User, CompanyProfile, CarrierProfile

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user(
            username='company_test',
            password='testpass123',
            email='company@test.com',
            role='company',
            company_name='Test Company',
            phone='+380 (50) 123 45 67'
        )
        self.carrier_user = User.objects.create_user(
            username='carrier_test',
            password='testpass123',
            email='carrier@test.com',
            role='carrier',
            phone='+380 (67) 987 65 43'
        )
    
    def test_company_creation(self):
        self.assertEqual(self.company_user.role, 'company')
        self.assertEqual(self.company_user.company_name, 'Test Company')
    
    def test_carrier_creation(self):
        self.assertEqual(self.carrier_user.role, 'carrier')


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            role='company'
        )
    
    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stays on login page
    
    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout


class CompanyRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_company_registration_page_loads(self):
        response = self.client.get(reverse('register_company'))
        self.assertEqual(response.status_code, 200)
    
    def test_company_registration(self):
        response = self.client.post(reverse('register_company'), {
            'username': 'newcompany',
            'email': 'new@company.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'company_name': 'New Company',
            'phone': '+380 (50) 111 22 33',
            'address': 'Test Address',
            'tax_id': '12345678'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newcompany').exists())


class CarrierRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_carrier_registration_page_loads(self):
        response = self.client.get(reverse('register_carrier'))
        self.assertEqual(response.status_code, 200)
    
    def test_carrier_registration(self):
        response = self.client.post(reverse('register_carrier'), {
            'username': 'newcarrier',
            'email': 'new@carrier.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'phone': '+380 (67) 222 33 44',
            'license_number': 'LIC123456',
            'vehicle_type': 'Вантажівка',
            'experience_years': 5
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newcarrier').exists())
