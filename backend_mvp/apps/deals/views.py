from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Deal
from .serializers import DealSerializer
from apps.payments.services import process_payout
from apps.contracts.services import generate_contract

class DealViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'worker':
            return Deal.objects.filter(worker=user)
        return Deal.objects.filter(customer=user)

    @action(detail=True, methods=['post'], url_path='confirm-worker')
    def confirm_worker(self, request, pk=None):
        deal = self.get_object()
        if request.user != deal.worker:
            return Response({"error": "Not your deal"}, status=403)
        
        deal.worker_confirmed = True
        deal.save()
        self._check_finish(deal)
        return Response({"status": "confirmed by worker"})

    @action(detail=True, methods=['post'], url_path='confirm-customer')
    def confirm_customer(self, request, pk=None):
        deal = self.get_object()
        if request.user != deal.customer:
            return Response({"error": "Not your deal"}, status=403)
        
        deal.customer_confirmed = True
        deal.save()
        self._check_finish(deal)
        return Response({"status": "confirmed by customer"})

    def _check_finish(self, deal):
        if deal.worker_confirmed and deal.customer_confirmed:
            deal.status = 'finished'
            deal.confirmed_at = timezone.now()
            deal.save()
            deal.order.status = 'finished'
            deal.order.save()
            
            # Trigger Services
            process_payout(deal)
            generate_contract(deal)
