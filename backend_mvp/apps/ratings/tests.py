"""
Rating System Tests

Comprehensive tests for rating calculation, fraud protection, and API endpoints.
"""

from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.deals.models import Deal
from apps.orders.models import Order
from apps.reviews.models import Review
from apps.ratings.models import RatingHistory, RatingProtectionLog, RatingConfig
from apps.ratings.services import RatingService, FraudProtectionService


User = get_user_model()


class RatingServiceTestCase(TestCase):
    """Tests for RatingService"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = User.objects.create_user(
            username='customer1',
            password='testpass123',
            role='customer'
        )
        self.worker = User.objects.create_user(
            username='worker1',
            password='testpass123',
            role='worker'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            title='Test Order',
            description='Test',
            price=100.00
        )
        self.deal = Deal.objects.create(
            order=self.order,
            customer=self.customer,
            worker=self.worker,
            status='finished'
        )
    
    def test_calculate_weighted_rating_no_reviews(self):
        """Test rating calculation with no reviews"""
        rating, count = RatingService.calculate_weighted_rating(self.worker)
        self.assertEqual(rating, Decimal('0.0'))
        self.assertEqual(count, 0)
    
    def test_calculate_weighted_rating_single_review(self):
        """Test rating calculation with single review"""
        Review.objects.create(
            deal=self.deal,
            from_user=self.customer,
            to_user=self.worker,
            rating=5,
            text='Great job!'
        )
        
        rating, count = RatingService.calculate_weighted_rating(self.worker)
        self.assertEqual(count, 1)
        self.assertGreater(rating, Decimal('4.5'))
    
    def test_recalculate_rating_creates_history(self):
        """Test that rating recalculation creates history entry"""
        Review.objects.create(
            deal=self.deal,
            from_user=self.customer,
            to_user=self.worker,
            rating=4,
            text='Good work'
        )
        
        old_rating = self.worker.rating
        new_rating = RatingService.recalculate_rating(
            self.worker, 
            reason='review_added'
        )
        
        # Check history was created
        history = RatingHistory.objects.filter(user=self.worker).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_rating, old_rating)
        self.assertEqual(history.new_rating, new_rating)
        self.assertEqual(history.reason, 'review_added')
    
    def test_get_user_rating_details(self):
        """Test rating details retrieval"""
        Review.objects.create(
            deal=self.deal,
            from_user=self.customer,
            to_user=self.worker,
            rating=4,
            text='Good'
        )
        
        RatingService.recalculate_rating(self.worker)
        details = RatingService.get_user_rating_details(self.worker)
        
        self.assertEqual(details['total_reviews'], 1)
        self.assertIn('distribution', details)
        self.assertEqual(details['distribution'][4], 1)


class FraudProtectionServiceTestCase(TestCase):
    """Tests for FraudProtectionService"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = User.objects.create_user(
            username='customer2',
            password='testpass123',
            role='customer'
        )
        self.worker = User.objects.create_user(
            username='worker2',
            password='testpass123',
            role='worker'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            title='Test Order 2',
            description='Test',
            price=100.00
        )
        self.deal = Deal.objects.create(
            order=self.order,
            customer=self.customer,
            worker=self.worker,
            status='finished'
        )
        RatingConfig.get_config()  # Ensure config exists
    
    def test_rate_limit_blocks_excessive_reviews(self):
        """Test that rate limit blocks excessive reviews"""
        config = RatingConfig.get_config()
        config.max_reviews_per_day = 2
        config.save()
        
        # Create reviews up to limit
        for i in range(2):
            order = Order.objects.create(
                customer=self.customer,
                title=f'Order {i}',
                description='Test',
                price=100.00
            )
            deal = Deal.objects.create(
                order=order,
                customer=self.customer,
                worker=self.worker,
                status='finished'
            )
            Review.objects.create(
                deal=deal,
                from_user=self.customer,
                to_user=self.worker,
                rating=5,
                text='Great!'
            )
        
        # Next should be blocked
        is_violation, reason = FraudProtectionService.check_rate_limit(
            self.customer, 
            config
        )
        self.assertTrue(is_violation)
        self.assertIn('лимит', reason)
    
    def test_circular_rating_detection(self):
        """Test circular rating detection is logged"""
        # First review: customer -> worker
        Review.objects.create(
            deal=self.deal,
            from_user=self.customer,
            to_user=self.worker,
            rating=5,
            text='Great!'
        )
        
        config = RatingConfig.get_config()
        
        # Check if worker -> customer would be flagged
        is_suspicious, warning = FraudProtectionService.check_circular_rating(
            self.worker,
            self.customer,
            config
        )
        
        # Should not block (bidirectional reviews are normal for deals)
        self.assertFalse(is_suspicious)
    
    def test_get_client_ip_from_forwarded(self):
        """Test IP extraction from X-Forwarded-For header"""
        mock_request = Mock()
        mock_request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.100, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1'
        }
        
        ip = FraudProtectionService.get_client_ip(mock_request)
        self.assertEqual(ip, '192.168.1.100')
    
    def test_get_client_ip_from_remote_addr(self):
        """Test IP extraction from REMOTE_ADDR"""
        mock_request = Mock()
        mock_request.META = {
            'REMOTE_ADDR': '192.168.1.200'
        }
        
        ip = FraudProtectionService.get_client_ip(mock_request)
        self.assertEqual(ip, '192.168.1.200')


class RatingAPITestCase(APITestCase):
    """Tests for Rating API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = User.objects.create_user(
            username='api_customer',
            password='testpass123',
            role='customer'
        )
        self.worker = User.objects.create_user(
            username='api_worker',
            password='testpass123',
            role='worker'
        )
        self.admin = User.objects.create_user(
            username='api_admin',
            password='testpass123',
            role='admin',
            is_staff=True
        )
        
        self.client = APIClient()
    
    def test_get_user_rating_authenticated(self):
        """Test getting user rating when authenticated"""
        self.client.force_authenticate(user=self.customer)
        
        response = self.client.get(f'/api/v1/ratings/{self.worker.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rating', response.data)
        self.assertIn('total_reviews', response.data)
    
    def test_get_user_rating_unauthenticated(self):
        """Test getting user rating when not authenticated"""
        response = self.client.get(f'/api/v1/ratings/{self.worker.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rating_history_own_user(self):
        """Test that user can see own rating history"""
        self.client.force_authenticate(user=self.worker)
        
        response = self.client.get(f'/api/v1/ratings/{self.worker.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rating_history_other_user_denied(self):
        """Test that user cannot see other's rating history"""
        self.client.force_authenticate(user=self.customer)
        
        response = self.client.get(f'/api/v1/ratings/{self.worker.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list for non-owner
        self.assertEqual(len(response.data), 0)
    
    def test_analytics_admin_only(self):
        """Test that analytics endpoint is admin-only"""
        # Non-admin attempt
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/ratings/analytics/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin attempt
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/ratings/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reviews', response.data)
    
    def test_recalculate_admin_only(self):
        """Test that recalculate endpoint is admin-only"""
        # Non-admin attempt
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(f'/api/v1/ratings/{self.worker.id}/recalculate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin attempt
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/v1/ratings/{self.worker.id}/recalculate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReviewIntegrationTestCase(APITestCase):
    """Integration tests for review creation with fraud protection"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = User.objects.create_user(
            username='int_customer',
            password='testpass123',
            role='customer'
        )
        self.worker = User.objects.create_user(
            username='int_worker',
            password='testpass123',
            role='worker'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            title='Integration Test Order',
            description='Test',
            price=100.00
        )
        self.deal = Deal.objects.create(
            order=self.order,
            customer=self.customer,
            worker=self.worker,
            status='finished'
        )
        
        RatingConfig.get_config()
        self.client = APIClient()
    
    def test_review_creation_updates_rating(self):
        """Test that creating review updates target user rating"""
        self.client.force_authenticate(user=self.customer)
        
        initial_rating = self.worker.rating
        
        response = self.client.post('/api/v1/reviews/', {
            'deal': self.deal.id,
            'rating': 5,
            'text': 'Excellent service!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check rating was updated
        self.worker.refresh_from_db()
        self.assertGreater(self.worker.rating, initial_rating)
        
        # Check history was created
        history = RatingHistory.objects.filter(user=self.worker).first()
        self.assertIsNotNone(history)
    
    def test_review_blocked_for_non_participant(self):
        """Test that non-participants cannot create review"""
        other_user = User.objects.create_user(
            username='other_user',
            password='testpass123'
        )
        self.client.force_authenticate(user=other_user)
        
        response = self.client.post('/api/v1/reviews/', {
            'deal': self.deal.id,
            'rating': 5,
            'text': 'Fake review'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_duplicate_review_blocked(self):
        """Test that duplicate reviews are blocked"""
        self.client.force_authenticate(user=self.customer)
        
        # First review
        response = self.client.post('/api/v1/reviews/', {
            'deal': self.deal.id,
            'rating': 5,
            'text': 'First review'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Duplicate attempt
        response = self.client.post('/api/v1/reviews/', {
            'deal': self.deal.id,
            'rating': 4,
            'text': 'Duplicate review'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
