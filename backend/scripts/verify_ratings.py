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
from apps.jobs.services import JobService, ApplicationService, CheckInService
from apps.ratings.models import Rating
from apps.users.models import UserType, BusinessProfile, WorkerProfile

User = get_user_model()

def run_verification():
    print("🚀 Starting Rating Verification...")
    
    # 1. Create Users
    print("\n1. Creating Users...")
    User.objects.filter(phone__in=['+996555888001', '+996555888002']).delete()
    
    business = User.objects.create_user(phone='+996555888001', password='password123', user_type=UserType.BUSINESS)
    BusinessProfile.objects.create(
        user=business, 
        company_name="Rate Corp", 
        bin="BIN888", 
        inn="INN888",
        contact_number="+996555888001"
    )
    
    worker = User.objects.create_user(phone='+996555888002', password='password123', user_type=UserType.WORKER)
    WorkerProfile.objects.create(user=worker, full_name="Rate Worker", verification_status='verified')
    
    # 2. Complete a Job
    print("\n2. Completing a Job...")
    job = Job.objects.create(
        business=business,
        title="Rating Job",
        description="To be rated",
        job_type=JobType.OTHER,
        date=timezone.now().date() + timedelta(days=1),
        start_time=(timezone.now() + timedelta(days=1)).time(),
        end_time=(timezone.now() + timedelta(days=1, hours=1)).time(),
        hourly_rate=Decimal('500.00'),
        workers_needed=1,
        location_lat=42.87,
        location_lng=74.56,
        location_address="Rate Addr",
        location_name="Rate Loc"
    )
    JobService.publish_job(job, business)
    app = ApplicationService.apply_to_job(job, worker)
    ApplicationService.accept_application(app, business)
    
    checkin = CheckInService.check_in(app, lat=42.87, lng=74.56)
    checkin.checked_in_at = timezone.now() - timedelta(hours=1) # Fake 1hr work
    checkin.save()
    CheckInService.check_out(checkin, lat=42.87, lng=74.56)
    
    JobService.complete_job(job, business)
    print(f"✅ Job {job.id} completed")
    
    # 3. Rate Worker (5 Stars)
    print("\n3. Business rates Worker (5 stars)...")
    rating1 = Rating.objects.create(
        rater=business,
        reviewee=worker,
        job=job,
        score=5,
        comment="Excellent worker!"
    )
    
    # Verify Worker Profile Update
    worker.worker_profile.refresh_from_db()
    print(f"Worker Rating: {worker.worker_profile.rating}")
    assert worker.worker_profile.rating == 5.00
    print("✅ Worker profile updated correctly")
    
    # 4. Rate Business (4 Stars)
    print("\n4. Worker rates Business (4 stars)...")
    rating2 = Rating.objects.create(
        rater=worker,
        reviewee=business,
        job=job,
        score=4,
        comment="Good business"
    )
    
    # Verify Business Profile Update
    business.business_profile.refresh_from_db()
    print(f"Business Rating: {business.business_profile.rating}")
    assert business.business_profile.rating == 4.00
    print("✅ Business profile updated correctly")
    
    # 5. Add another rating to verify average
    # Need another job for same pair or use `unique_together` constraint check?
    # Let's create another job quickly
    job2 = Job.objects.create(
        business=business,
        title="Job 2",
        job_type=JobType.OTHER,
        date=timezone.now().date() + timedelta(days=1),
        start_time=(timezone.now() + timedelta(days=1)).time(),
        end_time=(timezone.now() + timedelta(days=1, hours=1)).time(),
        hourly_rate=Decimal('500.00'),
        workers_needed=1,
        location_lat=42.87,
        location_lng=74.56
    )
    # Skipping flow, just forcing completion constraint logic check (RatingSerializer)
    # But here we use ORM directly.
    
    Rating.objects.create(
        rater=business,
        reviewee=worker,
        job=job2,
        score=3,
        comment="Average"
    )
    worker.worker_profile.refresh_from_db()
    # Avg of 5 and 3 is 4
    print(f"New Worker Rating: {worker.worker_profile.rating}")
    assert worker.worker_profile.rating == 4.00
    print("✅ Average calculation verified")

    print("\n✨ RATINGS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
