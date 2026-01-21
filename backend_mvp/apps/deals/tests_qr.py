from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.orders.models import Order
from apps.deals.models import Deal

User = get_user_model()

class QRCheckInTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username='cust', password='password', role='customer')
        self.worker = User.objects.create_user(username='work', password='password', role='worker')
        self.other = User.objects.create_user(username='other', password='password', role='worker')
        
        self.order = Order.objects.create(
            customer=self.customer,
            title='QR Task',
            description='Test QR',
            price=100.00
        )
        
        self.deal = Deal.objects.create(
            order=self.order,
            customer=self.customer,
            worker=self.worker,
            status='in_progress'
        )
        self.qr_url = f'/api/v1/deals/{self.deal.id}/qr-code/'
        self.checkin_url = f'/api/v1/deals/{self.deal.id}/check-in/'
        self.checkout_url = f'/api/v1/deals/{self.deal.id}/check-out/'

    def test_customer_can_get_qr(self):
        self.client.force_authenticate(user=self.customer)
        resp = self.client.get(self.qr_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('qr_token', resp.data)
        self.assertEqual(str(resp.data['qr_token']), str(self.deal.qr_token))

    def test_worker_cannot_get_qr(self):
        self.client.force_authenticate(user=self.worker)
        resp = self.client.get(self.qr_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_in_success(self):
        self.client.force_authenticate(user=self.worker)
        data = {
            'qr_token': str(self.deal.qr_token),
            'latitude': 42.87,
            'longitude': 74.59
        }
        resp = self.client.post(self.checkin_url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.status, 'started')
        self.assertIsNotNone(self.deal.started_at)
        self.assertAlmostEqual(float(self.deal.check_in_lat), 42.87, places=2)

    def test_check_in_invalid_token(self):
        self.client.force_authenticate(user=self.worker)
        data = {'qr_token': 'wrong-token'}
        resp = self.client.post(self.checkin_url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_out_success(self):
        # First check in
        self.deal.status = 'started'
        self.deal.save()
        
        self.client.force_authenticate(user=self.worker)
        data = {'qr_token': str(self.deal.qr_token)}
        resp = self.client.post(self.checkout_url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.status, 'waiting_confirm')
        self.assertIsNotNone(self.deal.finished_at)
