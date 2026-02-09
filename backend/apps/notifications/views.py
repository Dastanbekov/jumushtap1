"""
API Views for Notifications app.
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Device, Notification
from .serializers import DeviceSerializer, NotificationSerializer
from .services import NotificationService


class DeviceViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    """
    ViewSet for managing FCM devices.
    
    POST /devices/ - Register device
    DELETE /devices/{id}/ - Remove device
    """
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Register a device using logic from Service to handle duplicates.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data.get('registration_id')
        device_type = serializer.validated_data.get('device_type', 'android')
        
        device = NotificationService.register_device(
            user=request.user,
            token=token,
            device_type=device_type
        )
        
        # Return serialized instance
        return Response(
            DeviceSerializer(device).data,
            status=status.HTTP_201_CREATED
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notification history.
    
    GET /notifications/ - List notifications
    GET /notifications/{id}/ - Retrieve detailed notification
    POST /notifications/{id}/read/ - Mark as read
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def read_all(self, request):
        """Mark all notifications as read."""
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})
