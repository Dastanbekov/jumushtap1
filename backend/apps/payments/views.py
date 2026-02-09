"""
API Views for payments app.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from .models import Transaction, Escrow, Payout
from .serializers import TransactionSerializer, EscrowSerializer, PayoutSerializer
from .services import WebhookService
from core.permissions import IsBusiness, IsWorker

logger = logging.getLogger(__name__)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing transactions.
    
    Business sees transactions they paid for.
    Workers see transactions they received.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions based on user role."""
        user = self.request.user
        
        if user.user_type == 'business':
            return Transaction.objects.filter(business=user).order_by('-created_at')
        elif user.user_type == 'worker':
            return Transaction.objects.filter(worker=user).order_by('-created_at')
        
        return Transaction.objects.none()


class EscrowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing escrows.
    
    Business sees escrows for their jobs.
    Workers see escrows for their applications.
    """
    serializer_class = EscrowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter escrows based on user role."""
        user = self.request.user
        
        if user.user_type == 'business':
            return Escrow.objects.filter(
                transaction__business=user
            ).order_by('-held_at')
        elif user.user_type == 'worker':
            return Escrow.objects.filter(
                application__worker=user
            ).order_by('-held_at')
        
        return Escrow.objects.none()


class PayoutViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing payouts (workers only).
    """
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated, IsWorker]
    
    def get_queryset(self):
        """Workers see only their own payouts."""
        return Payout.objects.filter(
            worker=self.request.user
        ).order_by('-initiated_at')


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(APIView):
    """
    Webhook endpoint for PSP callbacks.
    
    POST /api/v1/payments/webhooks/psp/
    
    Handles payment_intent and transfer events from payment provider.
    """
    permission_classes = []  # No authentication for webhooks
    authentication_classes = []
    
    def post(self, request):
        """Handle incoming webhook."""
        payload = request.body
        signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        # Alternative signature headers for different PSPs
        if not signature:
            signature = request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
        
        logger.info(f"Webhook received: {len(payload)} bytes")
        
        try:
            result = WebhookService.handle_webhook(payload, signature)
            
            if result['success']:
                return HttpResponse(status=200)
            else:
                return HttpResponse(result['message'], status=400)
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            return HttpResponse(str(e), status=500)
