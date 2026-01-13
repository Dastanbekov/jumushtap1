from rest_framework import serializers
from .models import Response

class ResponseSerializer(serializers.ModelSerializer):
    worker_name = serializers.ReadOnlyField(source='worker.username')
    worker_rating = serializers.ReadOnlyField(source='worker.rating')
    
    class Meta:
        model = Response
        fields = ('id', 'order', 'worker', 'worker_name', 'worker_rating', 'text', 'status', 'created_at')
        read_only_fields = ('id', 'worker', 'status', 'created_at', 'worker_name', 'worker_rating')
