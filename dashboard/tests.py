from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import User

User = get_user_model()


class DashboardViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@test.com',
            role='company',
            company_name='Test Company'
        )
    
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_statistics_requires_login(self):
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_statistics_for_logged_user(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
    
    def test_history_requires_login(self):
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_history_for_logged_user(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
