from rest_framework import serializers
from .models import Deal

class DealSerializer(serializers.ModelSerializer):
    order_title = serializers.ReadOnlyField(source='order.title')
    customer_name = serializers.ReadOnlyField(source='customer.username')
    worker_name = serializers.ReadOnlyField(source='worker.username')

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ('status', 'worker_confirmed', 'customer_confirmed', 'confirmed_at', 'customer', 'worker', 'order')
