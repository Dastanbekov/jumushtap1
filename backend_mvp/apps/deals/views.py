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

    @action(detail=True, methods=['get'], url_path='qr-code')
    def get_qr(self, request, pk=None):
        """
        Get QR token (Customer only).
        """
        deal = self.get_object()
        if request.user != deal.customer:
             return Response({"error": "Access denied. Only customer can see QR."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"qr_token": deal.qr_token})

    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        """
        Worker scans Customer's QR to start work.
        """
        deal = self.get_object()
        if request.user != deal.worker:
            return Response({"error": "Access denied. Not your deal."}, status=status.HTTP_403_FORBIDDEN)
        
        token = request.data.get('qr_token')
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')

        if not token or str(token) != str(deal.qr_token):
             return Response({"error": "Invalid QR Token"}, status=status.HTTP_400_BAD_REQUEST)
        
        if deal.status != 'in_progress':
             return Response({"error": "Deal is not in pending start state."}, status=status.HTTP_400_BAD_REQUEST)
        
        deal.status = 'started'
        deal.started_at = timezone.now()
        if lat: deal.check_in_lat = lat
        if lon: deal.check_in_lon = lon
        deal.save()
        
        return Response({"status": "Work checked-in successfully", "started_at": deal.started_at})

    @action(detail=True, methods=['post'], url_path='check-out')
    def check_out(self, request, pk=None):
        """
        Worker scans QR (or manual) to finish work.
        """
        deal = self.get_object()
        if request.user != deal.worker:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
            
        if deal.status != 'started':
             return Response({"error": "Work has not started yet."}, status=status.HTTP_400_BAD_REQUEST)
        
        # If token provided, validate it. If not, maybe allow manual checkout (configurable)
        # For strict QR flow:
        token = request.data.get('qr_token')
        if token and str(token) != str(deal.qr_token):
             return Response({"error": "Invalid QR Token"}, status=status.HTTP_400_BAD_REQUEST)

        deal.status = 'waiting_confirm'
        deal.finished_at = timezone.now()
        deal.save()
        
        return Response({"status": "Work checked-out. Waiting for confirmation.", "finished_at": deal.finished_at})

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
