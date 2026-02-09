"""
Services for Jobs app.
Business logic for job matching, state transitions, and check-in/out.
"""

import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, F

from .models import Job, JobApplication, CheckIn, JobStatus, ApplicationStatus
from core.utils.geo import haversine_distance, is_within_radius, validate_coordinates, calculate_bounding_box

logger = logging.getLogger(__name__)


class JobMatchingService:
    """
    Service for matching workers to jobs based on location and requirements.
    """
    
    DEFAULT_RADIUS_KM = 10.0  # Default search radius
    MAX_RADIUS_KM = 50.0  # Maximum search radius
    
    @classmethod
    def find_nearby_jobs(cls, worker, lat, lng, radius_km=None, job_type=None, limit=20):
        """
        Find jobs near worker's location.
        
        Args:
            worker: CustomUser (worker)
            lat: Worker's current latitude
            lng: Worker's current longitude
            radius_km: Search radius in kilometers (default: 10km)
            job_type: Optional job type filter
            limit: Maximum results to return
        
        Returns:
            QuerySet of Job instances, ordered by distance
        """
        if radius_km is None:
            radius_km = cls.DEFAULT_RADIUS_KM
        
        # Validate coordinates
        is_valid, error = validate_coordinates(lat, lng)
        if not is_valid:
            logger.error(f"Invalid coordinates for worker {worker.id}: {error}")
            return Job.objects.none()
        
        # Cap radius
        radius_km = min(radius_km, cls.MAX_RADIUS_KM)
        
        # Calculate bounding box for efficient DB query
        bbox = calculate_bounding_box(lat, lng, radius_km)
        
        # Base queryset: published jobs not yet started
        queryset = Job.objects.filter(
            status=JobStatus.PUBLISHED,
            date__gte=timezone.now().date(),
        ).filter(
            # Bounding box filter (fast)
            location_lat__gte=bbox['min_lat'],
            location_lat__lte=bbox['max_lat'],
            location_lng__gte=bbox['min_lng'],
            location_lng__lte=bbox['max_lng'],
        ).exclude(
            # Exclude jobs worker already applied to
            applications__worker=worker
        ).filter(
            # Only jobs with available slots
            workers_accepted__lt=F('workers_needed')
        )
        
        # Optional job type filter
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Fetch jobs and calculate exact distances
        jobs_with_distance = []
        
        for job in queryset[:limit * 2]:  # Fetch more for precise filtering
            distance = haversine_distance(
                lat, lng,
                float(job.location_lat), float(job.location_lng)
            )
            
            if distance <= radius_km:
                job.distance_km = round(distance, 2)
                jobs_with_distance.append(job)
        
        # Sort by distance
        jobs_with_distance.sort(key=lambda j: j.distance_km)
        
        return jobs_with_distance[:limit]
    
    @classmethod
    def calculate_match_score(cls, worker, job):
        """
        Calculate match score between worker and job.
        
        Factors:
        - Worker rating
        - Completed jobs count
        - Skill match (if skills are tracked)
        
        Returns:
            float: Match score (0-100)
        """
        score = 50.0  # Base score
        
        try:
            profile = worker.worker_profile
            
            # Rating bonus (0-25 points)
            if profile.rating > 0:
                score += (float(profile.rating) / 5.0) * 25
            
            # Experience bonus (0-15 points)
            if profile.completed_jobs_count > 0:
                experience_score = min(profile.completed_jobs_count / 10.0, 1.0) * 15
                score += experience_score
            
            # Skill match bonus (0-10 points)
            if profile.skills and job.job_type in profile.skills:
                score += 10
            
        except Exception as e:
            logger.warning(f"Error calculating match score: {e}")
        
        return min(score, 100.0)


class JobService:
    """
    Service for job lifecycle management.
    """
    
    @staticmethod
    @transaction.atomic
    def publish_job(job, published_by):
        """
        Publish a job (transition from draft to published).
        
        Args:
            job: Job instance
            published_by: User publishing the job
        
        Returns:
            Job instance
        """
        # Validate ownership
        if job.business != published_by:
            raise PermissionError("Only job owner can publish")
        
        # Validate required fields
        if not all([job.title, job.date, job.start_time, job.end_time, job.hourly_rate]):
            raise ValueError("Missing required fields for publication")
        
        # Check date is in future
        job_datetime = datetime.combine(job.date, job.start_time)
        if job_datetime <= datetime.now():
            raise ValueError("Job date/time must be in the future")
        
        # Transition status
        job.transition_to(JobStatus.PUBLISHED)
        
        # Fraud Check: Job Velocity
        from apps.security.services import FraudService
        try:
            FraudService.check_job_velocity(published_by)
        except Exception as e:
            logger.error(f"Fraud check failed: {e}")
        
        logger.info(f"Job {job.id} published by {published_by.id}")
        
        # TODO: Send notifications to nearby workers (Phase 5)
        
        return job
    
    @staticmethod
    @transaction.atomic
    def start_job(job):
        """
        Start a job (transition to in_progress).
        Typically triggered when first worker checks in.
        """
        job.transition_to(JobStatus.IN_PROGRESS)
        logger.info(f"Job {job.id} started")
        return job
    
    @staticmethod
    @transaction.atomic
    def complete_job(job, completed_by):
        """
        Mark job as completed.
        Triggers payment processing (Phase 4).
        """
        # Validate ownership
        if job.business != completed_by:
            raise PermissionError("Only job owner can complete")
        
        job.transition_to(JobStatus.COMPLETED)
        logger.info(f"Job {job.id} completed by {completed_by.id}")
        
        # TODO: Trigger payment processing (Phase 4)
        
        return job
    
    @staticmethod
    @transaction.atomic
    def cancel_job(job, cancelled_by, reason=None):
        """
        Cancel a job.
        Handles refunds if applicable.
        """
        # Validate ownership
        if job.business != cancelled_by:
            raise PermissionError("Only job owner can cancel")
        
        job.transition_to(JobStatus.CANCELLED)
        logger.info(f"Job {job.id} cancelled by {cancelled_by.id}. Reason: {reason}")
        
        # Handle refunds for accepted applications
        from apps.payments.services import PaymentService
        from apps.payments.models import Transaction
        
        # Refund all escrows for this job
        transactions = Transaction.objects.filter(
            job=job,
            status__in=['pending', 'held']
        )
        
        for trans in transactions:
            try:
                PaymentService.refund_escrow(trans, reason=reason)
            except Exception as e:
                logger.error(f"Failed to refund transaction {trans.id}: {e}")
        
        return job


class ApplicationService:
    """
    Service for managing job applications.
    """
    
    @staticmethod
    @transaction.atomic
    def apply_to_job(job, worker, message=None):
        """
        Worker applies to a job.
        
        Args:
            job: Job instance
            worker: Worker user
            message: Optional application message
        
        Returns:
            JobApplication instance
        """
        # Validate job status
        if job.status != JobStatus.PUBLISHED:
            raise ValueError("Can only apply to published jobs")
        
        # Check if job is full
        if job.is_full:
            raise ValueError("Job is already full")
        
        # Check for existing application
        if JobApplication.objects.filter(job=job, worker=worker).exists():
            raise ValueError("Already applied to this job")
        
        # Check worker verification
        try:
            if worker.worker_profile.verification_status != 'verified':
                raise ValueError("Worker profile must be verified to apply")
        except AttributeError:
            raise ValueError("Worker profile not found")
        
        # Create application
        application = JobApplication.objects.create(
            job=job,
            worker=worker,
            message=message or ''
        )
        
        # Fraud Check: Application Velocity
        from apps.security.services import FraudService
        try:
            FraudService.check_application_velocity(worker)
        except Exception as e:
            logger.error(f"Fraud check failed: {e}")
            
        logger.info(f"Worker {worker.id} applied to job {job.id}")
        
        # Notify business
        from apps.notifications.services import NotificationService
        try:
            NotificationService.notify_application_received(job, application)
        except Exception as e:
            logger.error(f"Failed to notify business about application {application.id}: {e}")
        
        return application
    
    @staticmethod
    @transaction.atomic
    def accept_application(application, accepted_by):
        """
        Business accepts a worker's application.
        """
        # Validate ownership
        if application.job.business != accepted_by:
            raise PermissionError("Only job owner can accept applications")
        
        # Accept application (handles workers_accepted increment)
        application.accept()
        
        logger.info(f"Application {application.id} accepted by {accepted_by.id}")
        
        # Fraud Check: Collusion
        from apps.security.services import FraudService
        try:
            FraudService.check_collusion(application.worker, application.job.business)
        except Exception as e:
            logger.error(f"Fraud check failed: {e}")

        # Hold payment funds in escrow
        from apps.payments.services import PaymentService
        
        try:
            trans, escrow = PaymentService.create_escrow_for_application(application)
            logger.info(f"Escrow created: {escrow.id} for application {application.id}")
        except Exception as e:
            logger.error(f"Failed to create escrow for application {application.id}: {e}")
            # Don't fail the acceptance, escrow can be created later
        
        # Notify worker
        from apps.notifications.services import NotificationService
        try:
            NotificationService.notify_application_accepted(application)
        except Exception as e:
            logger.error(f"Failed to notify worker about application {application.id}: {e}")
        
        return application
    
    @staticmethod
    @transaction.atomic
    def reject_application(application, rejected_by):
        """
        Business rejects a worker's application.
        """
        # Validate ownership
        if application.job.business != rejected_by:
            raise PermissionError("Only job owner can reject applications")
        
        application.reject()
        
        logger.info(f"Application {application.id} rejected by {rejected_by.id}")
        
        # Notify worker
        from apps.notifications.services import NotificationService
        try:
            NotificationService.notify_application_rejected(application)
        except Exception as e:
            logger.error(f"Failed to notify worker about rejection {application.id}: {e}")
        
        return application


class CheckInService:
    """
    Service for check-in/check-out management with GPS validation.
    """
    
    MAX_CHECKIN_DISTANCE_KM = 0.1  # 100 meters
    
    @classmethod
    @transaction.atomic
    def check_in(cls, application, lat, lng, device_info=None):
        """
        Worker checks in to a job.
        
        Args:
            application: JobApplication instance (must be accepted)
            lat: Check-in latitude
            lng: Check-in longitude
            device_info: Optional device metadata
        
        Returns:
            CheckIn instance
        """
        # Validate application status
        if application.status != ApplicationStatus.ACCEPTED:
            raise ValueError("Can only check in to accepted applications")
        
        # Check if already checked in
        if hasattr(application, 'checkin'):
            raise ValueError("Already checked in")
        
        # Validate coordinates
        is_valid, error = validate_coordinates(lat, lng)
        if not is_valid:
            raise ValueError(f"Invalid coordinates: {error}")
        
        # Validate location (within 100m of job location)
        job = application.job
        distance = haversine_distance(
            lat, lng,
            float(job.location_lat), float(job.location_lng)
        )
        
        if distance > cls.MAX_CHECKIN_DISTANCE_KM:
            raise ValueError(
                f"Check-in location too far from job location ({distance:.2f}km). "
                f"Maximum distance: {cls.MAX_CHECKIN_DISTANCE_KM}km"
            )
        
        # Create check-in
        checkin = CheckIn.objects.create(
            application=application,
            checked_in_at=timezone.now(),
            check_in_lat=lat,
            check_in_lng=lng,
            device_info=device_info or {}
        )
        
        # Start job if not yet started
        if job.status == JobStatus.PUBLISHED:
            JobService.start_job(job)
        
        logger.info(f"Worker {application.worker.id} checked in to job {job.id}")
        
        # Notify business
        from apps.notifications.services import NotificationService
        try:
            NotificationService.notify_worker_checked_in(checkin)
        except Exception as e:
            logger.error(f"Failed to notify business about checkin {checkin.id}: {e}")
        
        return checkin
    
    @classmethod
    @transaction.atomic
    def check_out(cls, checkin, lat, lng, device_info=None):
        """
        Worker checks out from a job.
        
        Args:
            checkin: CheckIn instance
            lat: Checkout latitude
            lng: Checkout longitude
            device_info: Optional device metadata
        
        Returns:
            CheckIn instance
        """
        # Validate coordinates
        is_valid, error = validate_coordinates(lat, lng)
        if not is_valid:
            raise ValueError(f"Invalid coordinates: {error}")
        
        # Perform checkout
        checkin.checkout(lat, lng, device_info)
        
        logger.info(
            f"Worker {checkin.application.worker.id} checked out from job {checkin.application.job.id}. "
            f"Worked {checkin.worked_hours:.2f} hours"
        )
        
        # Notify business
        from apps.notifications.services import NotificationService
        try:
            NotificationService.notify_worker_checked_out(checkin)
        except Exception as e:
            logger.error(f"Failed to notify business about checkout {checkin.id}: {e}")
        
        # Trigger payment release after checkout
        from apps.payments.services import PaymentService
        
        try:
            payout = PaymentService.release_escrow_after_checkout(checkin)
            logger.info(f"Payment released: Payout {payout.id} for {payout.amount}")
        except Exception as e:
            logger.error(f"Failed to release payment for checkin {checkin.id}: {e}")
            # Don't fail checkout, payment can be processed later
        
        return checkin
    
    @staticmethod
    def validate_checkin_time(application):
        """
        Check if current time is within valid check-in window.
        Workers can check in up to 30 minutes before start time.
        """
        job = application.job
        job_start = datetime.combine(job.date, job.start_time)
        now = datetime.now()
        
        # Allow check-in 30 minutes before
        earliest_checkin = job_start - timedelta(minutes=30)
        
        if now < earliest_checkin:
            return False, f"Too early to check in. Job starts at {job_start}"
        
        # Allow check-in up to 30 minutes after start
        latest_checkin = job_start + timedelta(minutes=30)
        
        if now > latest_checkin:
            return False, f"Too late to check in. Job started at {job_start}"
        
        return True, "OK"
