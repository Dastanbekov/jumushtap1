from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.orders.models import Order
from apps.responses.models import Response
from apps.deals.models import Deal
from apps.payments.models import PayoutLog
from apps.contracts.models import Contract

User = get_user_model()

class MVPFlowTest(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cust', password='password', role='customer', email='c@test.com')
        self.worker = User.objects.create_user(username='work', password='password', role='worker', email='w@test.com')
        
    def test_full_flow(self):
        print("\n--- Starting End-to-End Flow Test ---")
        # 1. Login
        resp = self.client.post('/api/v1/auth/login/', {'username': 'cust', 'password': 'password'})
        self.assertEqual(resp.status_code, 200)
        cust_token = resp.data['access']
        print("Customer logged in")
        
        resp = self.client.post('/api/v1/auth/login/', {'username': 'work', 'password': 'password'})
        work_token = resp.data['access']
        print("Worker logged in")
        
        # 2. Create Order (Customer)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + cust_token)
        data = {'title': 'Fix Sink', 'description': 'Leaking faucet', 'price': 100.00}
        resp = self.client.post('/api/v1/orders/', data)
        self.assertEqual(resp.status_code, 201)
        order_id = resp.data['id']
        print(f"Order created: {order_id}")
        
        # 3. Respond (Worker)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + work_token)
        data = {'order': order_id, 'text': 'I can fix it'}
        resp = self.client.post('/api/v1/responses/', data)
        self.assertEqual(resp.status_code, 201)
        response_id = resp.data['id']
        print(f"Response created: {response_id}")
        
        # 4. Accept Response (Customer)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + cust_token)
        resp = self.client.post(f'/api/v1/responses/{response_id}/accept/')
        if resp.status_code != 200:
            print(resp.data)
        self.assertEqual(resp.status_code, 200)
        print("Response accepted, Deal created")
        
        # Check Deal matches
        deal = Deal.objects.get(order_id=order_id)
        self.assertEqual(deal.status, 'in_progress')
        
        # 5. Worker Confirm
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + work_token)
        resp = self.client.post(f'/api/v1/deals/{deal.id}/confirm-worker/')
        self.assertEqual(resp.status_code, 200)
        print("Worker confirmed")
        
        # 6. Customer Confirm
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + cust_token)
        resp = self.client.post(f'/api/v1/deals/{deal.id}/confirm-customer/')
        self.assertEqual(resp.status_code, 200)
        print("Customer confirmed")
        
        # Check Finished Status
        deal.refresh_from_db()
        self.assertEqual(deal.status, 'finished', "Deal status should be finished")
        
        # Check Payout
        payout = PayoutLog.objects.get(deal=deal)
        self.assertEqual(float(payout.amount), 90.00) 
        print(f"Payout generated: {payout.amount}")
        
        # Check Contract
        has_contract = Contract.objects.filter(deal=deal).exists()
        self.assertTrue(has_contract, "Contract should have been generated")
        print("Contract generated")

        print("--- Test Passed Successfully ---")
