from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import WorkerProfile, CustomerProfile

User = get_user_model()

class ProfileSignalTestCase(TestCase):
    def test_worker_profile_creation(self):
        user = User.objects.create_user(username='worker1', role='worker')
        self.assertTrue(hasattr(user, 'worker_profile'))
        self.assertIsInstance(user.worker_profile, WorkerProfile)

    def test_customer_profile_creation(self):
        user = User.objects.create_user(username='customer1', role='customer')
        self.assertTrue(hasattr(user, 'customer_profile'))
        self.assertIsInstance(user.customer_profile, CustomerProfile)

class ProfileAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.worker_user = User.objects.create_user(username='worker_api', password='password', role='worker')
        self.customer_user = User.objects.create_user(username='customer_api', password='password', role='customer')

    def test_get_extended_profile_worker(self):
        self.client.force_authenticate(user=self.worker_user)
        response = self.client.get('/api/v1/users/me/extended/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('skills', response.data) # Check specific field
        self.assertIn('passport_number', response.data)

    def test_update_extended_profile_worker(self):
        self.client.force_authenticate(user=self.worker_user)
        data = {
            'about': 'I am a strong worker',
            'experience_years': 5
        }
        response = self.client.patch('/api/v1/users/me/extended/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.worker_user.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_user.worker_profile.about, 'I am a strong worker')
        self.assertEqual(self.worker_user.worker_profile.experience_years, 5)

    def test_update_extended_profile_customer(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'company_name': 'Best Shop',
            'inn': '12345678901234'
        }
        response = self.client.patch('/api/v1/users/me/extended/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer_user.customer_profile.refresh_from_db()
        self.assertEqual(self.customer_user.customer_profile.company_name, 'Best Shop')
        self.assertEqual(self.customer_user.customer_profile.inn, '12345678901234')

    def test_verification_request(self):
        self.client.force_authenticate(user=self.worker_user)
        response = self.client.post('/api/v1/users/me/verify/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.worker_user.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_user.worker_profile.verification_status, 'pending')

    def test_nested_profile_in_user_serializer(self):
        self.client.force_authenticate(user=self.worker_user)
        response = self.client.get('/api/v1/users/me/')
        self.assertIn('profile', response.data)
        self.assertEqual(response.data['profile']['experience_years'], 0)
