"""
Serializers for Jobs app.
"""

from rest_framework import serializers
from decimal import Decimal

from .models import Job, JobApplication, CheckIn, JobType, JobStatus, ApplicationStatus
from apps.users.serializers import WorkerProfileSerializer


class JobListSerializer(serializers.ModelSerializer):
    """
    Serializer for job listing (read-only, with minimal info).
    """
    business_name = serializers.SerializerMethodField()
    distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
        required=False
    )
    available_slots = serializers.IntegerField(read_only=True)
    duration_hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Job
        fields = [
            'id',
            'job_type',
            'title',
            'date',
            'start_time',
            'end_time',
            'hourly_rate',
            'workers_needed',
            'workers_accepted',
            'available_slots',
            'duration_hours',
            'location_name',
            'location_address',
            'location_lat',
            'location_lng',
            'distance_km',
            'status',
            'business_name',
            'published_at',
        ]
        read_only_fields = fields
    
    def get_business_name(self, obj):
        """Get business company name."""
        try:
            return obj.business.business_profile.company_name
        except AttributeError:
            return "Unknown"


class JobDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for job details (includes full description).
    """
    business_name = serializers.SerializerMethodField()
    business_phone = serializers.SerializerMethodField()
    available_slots = serializers.IntegerField(read_only=True)
    duration_hours = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id',
            'job_type',
            'title',
            'description',
            'date',
            'start_time',
            'end_time',
            'hourly_rate',
            'workers_needed',
            'workers_accepted',
            'available_slots',
            'duration_hours',
            'total_cost',
            'location_name',
            'location_address',
            'location_lat',
            'location_lng',
            'requirements',
            'status',
            'business_name',
            'business_phone',
            'published_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_business_name(self, obj):
        try:
            return obj.business.business_profile.company_name
        except AttributeError:
            return "Unknown"
    
    def get_business_phone(self, obj):
        try:
            return str(obj.business.business_profile.contact_number)
        except AttributeError:
            return None


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating jobs.
    """
    class Meta:
        model = Job
        fields = [
            'job_type',
            'title',
            'description',
            'date',
            'start_time',
            'end_time',
            'hourly_rate',
            'workers_needed',
            'location_name',
            'location_address',
            'location_lat',
            'location_lng',
            'requirements',
        ]
    
    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive."""
        if value <= 0:
            raise serializers.ValidationError("Hourly rate must be positive")
        return value
    
    def validate_workers_needed(self, value):
        """Validate worker count."""
        if value < 1:
            raise serializers.ValidationError("At least 1 worker is required")
        if value > 50:
            raise serializers.ValidationError("Maximum 50 workers allowed")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # Check end time is after start time
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': "End time must be after start time"
                })
        
        # Validate coordinates
        from core.utils.geo import validate_coordinates
        
        if 'location_lat' in data and 'location_lng' in data:
            is_valid, error = validate_coordinates(
                data['location_lat'],
                data['location_lng']
            )
            if not is_valid:
                raise serializers.ValidationError({
                    'location_lat': error
                })
        
        return data


class JobApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for job applications.
    """
    worker_name = serializers.SerializerMethodField()
    worker_rating = serializers.SerializerMethodField()
    worker_completed_jobs = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id',
            'job',
            'job_title',
            'worker',
            'worker_name',
            'worker_rating',
            'worker_completed_jobs',
            'status',
            'message',
            'applied_at',
            'responded_at',
        ]
        read_only_fields = ['id', 'status', 'applied_at', 'responded_at']
    
    def get_worker_name(self, obj):
        try:
            return obj.worker.worker_profile.full_name
        except AttributeError:
            return "Unknown"
    
    def get_worker_rating(self, obj):
        try:
            return float(obj.worker.worker_profile.rating)
        except AttributeError:
            return 0.0
    
    def get_worker_completed_jobs(self, obj):
        try:
            return obj.worker.worker_profile.completed_jobs_count
        except AttributeError:
            return 0


class ApplyToJobSerializer(serializers.Serializer):
    """
    Serializer for applying to a job.
    """
    job_id = serializers.UUIDField(required=True)
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class CheckInSerializer(serializers.ModelSerializer):
    """
    Serializer for check-in/check-out.
    """
    worker_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    worked_hours = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = CheckIn
        fields = [
            'id',
            'application',
            'job_title',
            'worker_name',
            'checked_in_at',
            'check_in_lat',
            'check_in_lng',
            'checked_out_at',
            'check_out_lat',
            'check_out_lng',
            'worked_hours',
            'is_checked_out',
        ]
        read_only_fields = [
            'id',
            'checked_in_at',
            'checked_out_at',
            'worked_hours',
            'is_checked_out',
        ]
    
    def get_worker_name(self, obj):
        try:
            return obj.application.worker.worker_profile.full_name
        except AttributeError:
            return "Unknown"


class PerformCheckInSerializer(serializers.Serializer):
    """
    Serializer for performing check-in.
    """
    application_id = serializers.UUIDField(required=True)
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    device_info = serializers.JSONField(required=False)


class PerformCheckOutSerializer(serializers.Serializer):
    """
    Serializer for performing check-out.
    """
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    device_info = serializers.JSONField(required=False)
