"""
URL Configuration for payments app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet, EscrowViewSet, PayoutViewSet, WebhookView

app_name = 'payments'

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'escrows', EscrowViewSet, basename='escrow')
router.register(r'payouts', PayoutViewSet, basename='payout')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/psp/', WebhookView.as_view(), name='webhook'),
]
