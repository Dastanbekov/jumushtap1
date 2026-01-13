from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Response as JobResponse
from .serializers import ResponseSerializer
from apps.orders.models import Order
from apps.deals.models import Deal
from apps.common.permissions import IsWorker, IsCustomer

class ResponseViewSet(viewsets.ModelViewSet):
    queryset = JobResponse.objects.all()
    serializer_class = ResponseSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsWorker()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.status != 'open':
            raise serializers.ValidationError("Order is not open.")
        serializer.save(worker=self.request.user)

    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            if self.request.user == order.customer:
                return JobResponse.objects.filter(order=order)
            elif self.request.user.role == 'worker':
                 return JobResponse.objects.filter(order=order, worker=self.request.user)
        
        user = self.request.user
        if user.role == 'worker':
            return JobResponse.objects.filter(worker=user)
        else:
            return JobResponse.objects.filter(order__customer=user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        response = self.get_object()
        order = response.order
        
        if order.customer != request.user:
            return Response({"error": "Not your order."}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status != 'open':
             return Response({"error": "Order already taken or closed."}, status=status.HTTP_400_BAD_REQUEST)
        
        response.status = 'accepted'
        response.save()
        
        order.status = 'in_progress'
        order.save()
        
        JobResponse.objects.filter(order=order).exclude(id=response.id).update(status='rejected')
        
        Deal.objects.create(
            order=order,
            customer=order.customer,
            worker=response.worker
        )
        
        return Response({"status": "accepted, deal created"})
