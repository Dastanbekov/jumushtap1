from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.username')
    customer_rating = serializers.ReadOnlyField(source='customer.rating')

    class Meta:
        model = Order
        fields = ('id', 'customer', 'customer_name', 'customer_rating', 'title', 'description', 'price', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'customer', 'status', 'created_at', 'updated_at', 'customer_name', 'customer_rating')
