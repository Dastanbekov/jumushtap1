"""
Serializers for payments app.
"""

from rest_framework import serializers
from .models import Transaction, Escrow, Payout


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction details.
    """
    business_name = serializers.SerializerMethodField()
    worker_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'job',
            'job_title',
            'business',
            'business_name',
            'worker',
            'worker_name',
            'amount',
            'platform_fee',
            'worker_payout',
            'status',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = fields
    
    def get_business_name(self, obj):
        try:
            return obj.business.business_profile.company_name
        except AttributeError:
            return str(obj.business.phone)
    
    def get_worker_name(self, obj):
        try:
            return obj.worker.worker_profile.full_name
        except AttributeError:
            return str(obj.worker.phone)


class EscrowSerializer(serializers.ModelSerializer):
    """
    Serializer for escrow details.
    """
    transaction = TransactionSerializer(read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    
    class Meta:
        model = Escrow
        fields = [
            'id',
            'transaction',
            'application',
            'job_title',
            'held_amount',
            'status',
            'held_at',
            'released_at',
            'auto_release_hours',
        ]
        read_only_fields = fields


class PayoutSerializer(serializers.ModelSerializer):
    """
    Serializer for payout details.
    """
    transaction_id = serializers.UUIDField(source='transaction.id', read_only=True)
    job_title = serializers.CharField(source='transaction.job.title', read_only=True)
    
    class Meta:
        model = Payout
        fields = [
            'id',
            'transaction_id',
            'job_title',
            'worker',
            'amount',
            'status',
            'transfer_id',
            'failure_reason',
            'retry_count',
            'initiated_at',
            'completed_at',
            'failed_at',
        ]
        read_only_fields = fields
