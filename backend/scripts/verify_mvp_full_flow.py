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
from apps.jobs.models import Job, JobType, JobStatus, JobApplication
from apps.jobs.services import JobService, ApplicationService, CheckInService
from apps.payments.models import Transaction, Escrow, Payout
from apps.payments.services import PaymentService
from apps.notifications.models import Notification, Device
from apps.notifications.services import NotificationService
from apps.ratings.models import Rating
from apps.security.models import SuspiciousActivity
from apps.users.models import UserType, BusinessProfile, WorkerProfile

User = get_user_model()

def run_e2e_verification():
    print("🌟 Starting Master E2E MVP Verification...")
    
    # Prefix for unique identification in this run
    TAG = "E2E_"
    B_PHONE = "+996111000001"
    W_PHONE = "+996111000002"
    
    # 1. Cleanup & Setup
    print("\n1. Setting up Users...")
    User.objects.filter(phone__in=[B_PHONE, W_PHONE]).delete()
    
    business = User.objects.create_user(phone=B_PHONE, password='password123', user_type=UserType.BUSINESS)
    BusinessProfile.objects.create(
        user=business, 
        company_name=f"{TAG}Corp", 
        bin=f"{TAG}BIN", 
        inn=f"{TAG}INN",
        contact_number=B_PHONE
    )
    
    worker = User.objects.create_user(phone=W_PHONE, password='password123', user_type=UserType.WORKER)
    WorkerProfile.objects.create(user=worker, full_name=f"{TAG}Worker", verification_status='verified')
    
    # Register Devices for Notifications
    NotificationService.register_device(business, f"{TAG}B_TOKEN", "ios")
    NotificationService.register_device(worker, f"{TAG}W_TOKEN", "android")
    
    # 2. Job Lifecycle
    print("\n2. Processing Job Lifecycle...")
    job = Job.objects.create(
        business=business,
        title=f"{TAG} Master Shift",
        description="Full E2E test shift",
        job_type=JobType.OTHER,
        date=timezone.now().date() + timedelta(days=1),
        start_time=(timezone.now() + timedelta(days=1)).time(),
        end_time=(timezone.now() + timedelta(days=1, hours=2)).time(),
        hourly_rate=Decimal('1000.00'),
        workers_needed=1,
        location_lat=42.87,
        location_lng=74.56,
        location_address="E2E Square",
        location_name="HQ"
    )
    
    JobService.publish_job(job, business)
    print("✅ Job published")
    
    app = ApplicationService.apply_to_job(job, worker, message="I can do this!")
    print("✅ Worker applied")
    
    # Check Business Notification
    b_notif = Notification.objects.filter(user=business, data__type="application_received").exists()
    assert b_notif, "Business did not receive application notification"
    print("✅ Business notification verified")
    
    ApplicationService.accept_application(app, business)
    print("✅ Application accepted")
    
    # Check Escrow
    escrow = Escrow.objects.filter(transaction__job=job).first()
    assert escrow and escrow.status == 'held', "Escrow not created or not held"
    print(f"✅ Escrow verified: {escrow.held_amount} KGS held")
    
    # Check Worker Notification
    w_notif = Notification.objects.filter(user=worker, data__type="application_accepted").exists()
    assert w_notif, "Worker did not receive acceptance notification"
    print("✅ Worker notification verified")
    
    # 3. Work Flow
    print("\n3. Processing Work Flow...")
    # Simulate work
    checkin = CheckInService.check_in(app, lat=42.87, lng=74.56)
    checkin.checked_in_at = timezone.now() - timedelta(hours=2)
    checkin.save()
    print("✅ Worker checked in (simulated 2 hours ago)")
    
    CheckInService.check_out(checkin, lat=42.87, lng=74.56)
    print("✅ Worker checked out")
    
    # Check Payout
    payout = Payout.objects.filter(transaction__job=job).first()
    assert payout and payout.status in ['processing', 'completed'], f"Payout status invalid: {payout.status if payout else 'None'}"
    print(f"✅ Payout verified: {payout.amount} KGS transferred to worker")
    
    # 4. Finalization
    print("\n4. Finalizing Job & Ratings...")
    JobService.complete_job(job, business)
    print("✅ Job completed")
    
    # 5. Ratings
    Rating.objects.create(rater=business, reviewee=worker, job=job, score=5, comment="Great E2E test!")
    Rating.objects.create(rater=worker, reviewee=business, job=job, score=5, comment="Paid on time!")
    
    worker.worker_profile.refresh_from_db()
    business.business_profile.refresh_from_db()
    
    assert worker.worker_profile.rating == 5.0, "Worker rating mismatch"
    assert business.business_profile.rating == 5.0, "Business rating mismatch"
    print("✅ Two-way ratings verified")
    
    # 6. Fraud Checks (Smoke check)
    print("\n5. Security Smoke Check...")
    # Velocity check (should NOT trigger for this single flow)
    flags = SuspiciousActivity.objects.filter(user__in=[business, worker])
    assert flags.count() == 0, "Unexpected fraud flags found"
    print("✅ No false positive fraud flags")

    print("\n🏆 E2E MVP MASTER VERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    try:
        run_e2e_verification()
    except Exception as e:
        print(f"\n❌ E2E VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
