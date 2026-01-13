from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order
from .serializers import OrderSerializer
from apps.common.permissions import IsOwnerOrReadOnly, IsCustomer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy', 'cancel']:
             return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['put'], url_path='cancel')
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != 'open':
            return Response(
                {"error": "Cannot cancel an order that is not open."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'canceled'
        order.save()
        return Response({"status": "order canceled"})
