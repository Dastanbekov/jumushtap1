"""
Serializers for Notifications app.
"""

from rest_framework import serializers
from .models import Device, Notification


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for registering/updating FCM devices.
    """
    class Meta:
        model = Device
        fields = ['id', 'registration_id', 'device_type', 'active', 'last_used_at']
        read_only_fields = ['id', 'last_used_at']
    
    def create(self, validated_data):
        # Handle user automatically from context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing notification history.
    """
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'data', 'is_read', 'created_at']
        read_only_fields = fields
