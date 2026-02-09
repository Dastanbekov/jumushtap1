from rest_framework import serializers
from .models import Rating
from apps.jobs.models import Job, JobStatus

class RatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.CharField(source='rater.full_name', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'rater', 'rater_name', 'reviewee', 'job', 'score', 'comment', 'tags', 'created_at']
        read_only_fields = ['id', 'rater', 'created_at']
        
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        job = attrs.get('job')
        reviewee = attrs.get('reviewee')
        
        # 1. Job must be COMPLETED
        if job.status != JobStatus.COMPLETED:
            raise serializers.ValidationError("Can only rate completed jobs.")
            
        # 2. User must be part of the job
        # If user is worker -> must be rating business
        if user.is_worker:
            # Check if user was accepted applicant
            # Actually need to check applications
            is_participant = job.applications.filter(worker=user, status='accepted').exists()
            if not is_participant:
                raise serializers.ValidationError("You did not participate in this job.")
            
            if reviewee != job.business:
                raise serializers.ValidationError("Worker can only rate the business owner of the job.")
                
        # If user is business -> must be rating worker
        elif user.is_business:
            if job.business != user:
                raise serializers.ValidationError("You do not own this job.")
                
            # Check if reviewee was worker
            is_worker = job.applications.filter(worker=reviewee, status='accepted').exists()
            if not is_worker:
                raise serializers.ValidationError("This worker did not participate in this job.")
                
        return attrs
        
    def create(self, validated_data):
        validated_data['rater'] = self.context['request'].user
        return super().create(validated_data)
