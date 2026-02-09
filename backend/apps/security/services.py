from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import SuspiciousActivity
from apps.jobs.models import Job, JobApplication

class FraudService:
    @staticmethod
    def check_job_velocity(user):
        """
        Check if user is creating too many jobs too quickly.
        Threshold: > 3 jobs in 10 minutes.
        """
        if not user.is_business:
            return
            
        time_threshold = timezone.now() - timedelta(minutes=10)
        recent_jobs = Job.objects.filter(business=user, created_at__gte=time_threshold).count()
        
        if recent_jobs > 3:
            SuspiciousActivity.objects.create(
                user=user,
                reason="High Job Creation Velocity",
                severity=SuspiciousActivity.Severity.MEDIUM,
                payload={"recent_jobs_count": recent_jobs, "window_minutes": 10}
            )
            # Potentially block action here or just log?
            # For now just log.
            
    @staticmethod
    def check_application_velocity(user):
        """
        Check if user is applying to too many jobs too quickly.
        Threshold: > 10 applications in 5 minutes.
        """
        if not user.is_worker:
            return
            
        time_threshold = timezone.now() - timedelta(minutes=5)
        recent_apps = JobApplication.objects.filter(worker=user, applied_at__gte=time_threshold).count()
        
        if recent_apps > 10:
             SuspiciousActivity.objects.create(
                user=user,
                reason="High Application Velocity",
                severity=SuspiciousActivity.Severity.MEDIUM,
                payload={"recent_apps_count": recent_apps, "window_minutes": 5}
            )
            
    @staticmethod
    def check_collusion(worker, business):
        """
        Check if worker and business are repeatedly working together excessively.
        Threshold: > 5 completed jobs in 1 week.
        """
        time_threshold = timezone.now() - timedelta(days=7)
        # Count completed jobs between them
        # Jobs where business=business AND application.worker=worker AND status=COMPLETED
        
        # Hard to query directly efficiently without complex join, assuming Application links them
        # Better: Query Applications accepted/completed
        
        interaction_count = JobApplication.objects.filter(
            worker=worker,
            job__business=business,
            status='completed', # or whatever completed status is for application? Application status is 'accepted'? No, Job status is COMPLETED.
            # Application doesn't have COMPLETED status separately usually, it stays accepted.
            # But Job has COMPLETED.
            job__status='completed',
            job__created_at__gte=time_threshold
        ).count()
        
        if interaction_count > 5:
            SuspiciousActivity.objects.create(
                user=worker, # Flag checking on worker side
                reason="Potential Collusion with Business",
                severity=SuspiciousActivity.Severity.HIGH,
                payload={"business_id": str(business.id), "interaction_count": interaction_count}
            )
            SuspiciousActivity.objects.create(
                user=business, # Flag checking on business side
                reason="Potential Collusion with Worker",
                severity=SuspiciousActivity.Severity.HIGH,
                payload={"worker_id": str(worker.id), "interaction_count": interaction_count}
            )
