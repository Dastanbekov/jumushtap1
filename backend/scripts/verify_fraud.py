import os
import sys
import django
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Job, JobType, JobStatus
from apps.jobs.services import JobService, ApplicationService
from apps.security.models import SuspiciousActivity
from apps.users.models import UserType, BusinessProfile, WorkerProfile

User = get_user_model()

def run_verification():
    print("🚀 Starting Fraud Detection Verification...")
    
    # Setup users
    User.objects.filter(phone__in=['+996555777001', '+996555777002']).delete()
    
    business = User.objects.create_user(phone='+996555777001', password='pass', user_type=UserType.BUSINESS)
    BusinessProfile.objects.create(
        user=business, 
        company_name="Fraud Test Corp",
        bin="BIN777777",
        inn="INN777777"
    )
    
    worker = User.objects.create_user(phone='+996555777002', password='pass', user_type=UserType.WORKER)
    WorkerProfile.objects.create(user=worker, full_name="Fraud Test Worker", verification_status='verified')
    
    # 1. Test Job Velocity (Threshold > 3 in 10 mins)
    print("\n1. Testing Job Velocity Limit...")
    for i in range(5):
        job = Job.objects.create(
            business=business,
            title=f"Spam Job {i}",
            job_type=JobType.OTHER,
            date=timezone.now().date() + timedelta(days=1), # Future
            start_time=(timezone.now() + timedelta(days=1)).time(),
            end_time=(timezone.now() + timedelta(days=1, hours=1)).time(),
            workers_needed=1,
            hourly_rate=Decimal('500.00'),
            location_lat=42.87,
            location_lng=74.56
        )
        JobService.publish_job(job, business)
        print(f"Published job {i+1}")
        
    # Check SuspiciousActivity
    flags = SuspiciousActivity.objects.filter(user=business, reason="High Job Creation Velocity")
    print(f"Flags found: {flags.count()}")
    assert flags.count() > 0
    print("✅ Job Velocity flagged correctly")
    
    # 2. Test Application Velocity (Threshold > 10 in 5 mins)
    # Reusing one job or creating many? Apply to same job is prevented?
    # ApplicationService logic usually prevents duplicate application to SAME job.
    # So we need multple jobs.
    print("\n2. Testing Application Velocity Limit...")
    
    # Create 12 dummy jobs
    jobs = []
    for i in range(12):
        j = Job.objects.create(
            business=business,
            title=f"App Job {i}",
            job_type=JobType.OTHER,
            date=timezone.now().date() + timedelta(days=2),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            workers_needed=1,
            hourly_rate=Decimal('500.00'),
            location_lat=42.87,
            location_lng=74.56
        )
        # Verify job is published? Service checks velocity on publish, but application service checks on apply.
        # Job needs to be published or open? apply_to_job checks nothing about job status? Usually checked manually.
        # But let's assume valid.
        j.status = JobStatus.PUBLISHED
        j.save()
        jobs.append(j)
        
    for i, job in enumerate(jobs):
        try:
            ApplicationService.apply_to_job(job, worker)
            print(f"Applied to job {i+1}")
        except Exception as e:
            print(f"Application failed: {e}")
            
    flags = SuspiciousActivity.objects.filter(user=worker, reason="High Application Velocity")
    print(f"Flags found: {flags.count()}")
    assert flags.count() > 0
    print("✅ Application Velocity flagged correctly")

    print("\n✨ FRAUD SYSTEM VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
