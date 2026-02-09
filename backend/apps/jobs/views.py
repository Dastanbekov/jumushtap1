"""
API Views for Jobs app.
Handles CRUD for jobs, applications, and check-in/out.
"""

import logging
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Job, JobApplication, CheckIn, JobStatus, ApplicationStatus
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    JobCreateUpdateSerializer,
    JobApplicationSerializer,
    ApplyToJobSerializer,
    CheckInSerializer,
    PerformCheckInSerializer,
    PerformCheckOutSerializer,
)
from .services import JobMatchingService, JobService, ApplicationService, CheckInService
from .permissions import (
    IsJobOwner,
    IsApplicationOwner,
    IsJobOwnerOrApplicationOwner,
    CanApplyToJobs,
)
from core.permissions import IsBusiness, IsWorker

logger = logging.getLogger(__name__)


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Job CRUD operations.
    
    list: Get all jobs (for business: own jobs, for worker: published jobs nearby)
    retrieve: Get job details
    create: Create new job (business only)
    update/partial_update: Update job (business owner only)
    destroy: Delete job (business owner only, if not started)
    
    Custom actions:
    - publish: Publish a draft job
    - complete: Mark job as completed
    - cancel: Cancel a job
    - applications: List applications for a job
    - search_nearby: Search jobs by location (worker)
    """
    
    queryset = Job.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        elif self.action == 'retrieve':
            return JobDetailSerializer
        return JobListSerializer
    
    def get_permissions(self):
        """
        Custom permissions per action.
        """
        if self.action in ['create', 'publish']:
            permission_classes = [IsAuthenticated, IsBusiness]
        elif self.action in ['update', 'partial_update', 'destroy', 'complete', 'cancel']:
            permission_classes = [IsAuthenticated, IsJobOwner]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on user role.
        """
        user = self.request.user
        
        # Business sees own jobs
        if user.user_type == 'business':
            return Job.objects.filter(business=user).order_by('-created_at')
        
        # Workers see published jobs
        elif user.user_type == 'worker':
            return Job.objects.filter(status=JobStatus.PUBLISHED).order_by('-published_at')
        
        # Admin sees all
        return Job.objects.all()
    
    def perform_create(self, serializer):
        """Create job with current user as business."""
        serializer.save(business=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish a draft job.
        POST /api/v1/jobs/{id}/publish/
        """
        job = self.get_object()
        
        try:
            JobService.publish_job(job, request.user)
            return Response({
                'message': 'Job published successfully',
                'job': JobDetailSerializer(job).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark job as completed.
        POST /api/v1/jobs/{id}/complete/
        """
        job = self.get_object()
        
        try:
            JobService.complete_job(job, request.user)
            return Response({
                'message': 'Job completed successfully',
                'job': JobDetailSerializer(job).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a job.
        POST /api/v1/jobs/{id}/cancel/
        Body: {"reason": "optional reason"}
        """
        job = self.get_object()
        reason = request.data.get('reason')
        
        try:
            JobService.cancel_job(job, request.user, reason)
            return Response({
                'message': 'Job cancelled successfully',
                'job': JobDetailSerializer(job).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """
        List all applications for a job (business owner only).
        GET /api/v1/jobs/{id}/applications/
        """
        job = self.get_object()
        
        # Check ownership
        if job.business != request.user:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        applications = job.applications.all()
        serializer = JobApplicationSerializer(applications, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search_nearby(self, request):
        """
        Search jobs near worker's location.
        POST /api/v1/jobs/search_nearby/
        Body: {
            "lat": 42.8746,
            "lng": 74.5698,
            "radius_km": 10,  # optional
            "job_type": "waiter"  # optional
        }
        """
        # Only workers can search
        if request.user.user_type != 'worker':
            return Response({
                'error': 'Only workers can search for jobs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        radius_km = request.data.get('radius_km')
        job_type = request.data.get('job_type')
        
        if not lat or not lng:
            return Response({
                'error': 'Latitude and longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find nearby jobs
        jobs = JobMatchingService.find_nearby_jobs(
            request.user,
            float(lat),
            float(lng),
            radius_km=float(radius_km) if radius_km else None,
            job_type=job_type
        )
        
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for job applications.
    
    list: My applications (as worker)
    create: Apply to a job
    destroy: Withdraw application
    
    Custom actions:
    - accept: Accept application (business only)
    - reject: Reject application (business only)
    """
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter based on user role."""
        user = self.request.user
        
        # Worker sees own applications
        if user.user_type == 'worker':
            return JobApplication.objects.filter(worker=user).order_by('-applied_at')
        
        # Business sees applications to their jobs
        elif user.user_type == 'business':
            return JobApplication.objects.filter(job__business=user).order_by('-applied_at')
        
        return JobApplication.objects.none()
    
    def create(self, request):
        """
        Apply to a job.
        POST /api/v1/applications/
        Body: {"job_id": "uuid", "message": "optional"}
        """
        serializer = ApplyToJobSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_id = serializer.validated_data['job_id']
        message = serializer.validated_data.get('message', '')
        
        job = get_object_or_404(Job, id=job_id)
        
        try:
            application = ApplicationService.apply_to_job(
                job,
                request.user,
                message
            )
            
            return Response(
                JobApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Withdraw application."""
        application = self.get_object()
        
        # Only worker can withdraw
        if application.worker != request.user:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            application.withdraw()
            return Response({
                'message': 'Application withdrawn successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept application (business only).
        POST /api/v1/applications/{id}/accept/
        """
        application = self.get_object()
        
        try:
            ApplicationService.accept_application(application, request.user)
            return Response({
                'message': 'Application accepted successfully',
                'application': JobApplicationSerializer(application).data
            })
        except (PermissionError, ValueError) as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject application (business only).
        POST /api/v1/applications/{id}/reject/
        """
        application = self.get_object()
        
        try:
            ApplicationService.reject_application(application, request.user)
            return Response({
                'message': 'Application rejected',
                'application': JobApplicationSerializer(application).data
            })
        except (PermissionError, ValueError) as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckInViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for check-in/out management.
    
    list: My check-ins (as worker)
    retrieve: Get check-in details
    
    Custom actions:
    - checkin: Perform check-in
    - checkout: Perform check-out
    """
    serializer_class = CheckInSerializer
    permission_classes = [IsAuthenticated, IsWorker]
    
    def get_queryset(self):
        """Worker sees own check-ins."""
        return CheckIn.objects.filter(
            application__worker=self.request.user
        ).order_by('-checked_in_at')
    
    @action(detail=False, methods=['post'])
    def checkin(self, request):
        """
        Perform check-in.
        POST /api/v1/checkins/checkin/
        Body: {
            "application_id": "uuid",
            "lat": 42.8746,
            "lng": 74.5698,
            "device_info": {}  # optional
        }
        """
        serializer = PerformCheckInSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application_id = serializer.validated_data['application_id']
        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        device_info = serializer.validated_data.get('device_info')
        
        application = get_object_or_404(
            JobApplication,
            id=application_id,
            worker=request.user
        )
        
        try:
            checkin = CheckInService.check_in(
                application,
                lat,
                lng,
                device_info
            )
            
            return Response(
                CheckInSerializer(checkin).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """
        Perform check-out.
        POST /api/v1/checkins/{id}/checkout/
        Body: {
            "lat": 42.8746,
            "lng": 74.5698,
            "device_info": {}  # optional
        }
        """
        checkin = self.get_object()
        serializer = PerformCheckOutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        device_info = serializer.validated_data.get('device_info')
        
        try:
            CheckInService.check_out(checkin, lat, lng, device_info)
            
            return Response(
                CheckInSerializer(checkin).data
            )
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
