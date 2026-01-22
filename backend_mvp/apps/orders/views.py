from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order
from .serializers import OrderSerializer
from apps.common.permissions import IsOwnerOrReadOnly, IsCustomer
from .services import MatchingService

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

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get orders within N km radius.
        QP: latitude, longitude, radius_km (default 50)
        """
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        try:
            radius = float(request.query_params.get('radius_km', 50))
        except ValueError:
            return Response({"error": "Invalid radius"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lat or not lon:
            return Response({"error": "Latitude and longitude required"}, status=status.HTTP_400_BAD_REQUEST)

        # Naive implementation: fetch all open orders and filter in Python.
        # Ideally: Use PostGIS 'dwithin'.
        orders = Order.objects.filter(status='open')
        valid_orders = []
        
        for order in orders:
            dist = MatchingService.calculate_distance(lat, lon, order.latitude, order.longitude)
            if dist <= radius:
                # Serialize and append distance
                data = OrderSerializer(order).data
                data['distance_km'] = round(dist, 1)
                valid_orders.append(data)
        
        # Sort by distance
        valid_orders.sort(key=lambda x: x['distance_km'])
        
        return Response(valid_orders)
