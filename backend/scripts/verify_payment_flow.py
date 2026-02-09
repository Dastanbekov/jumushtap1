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
from apps.jobs.models import Job, JobType
from apps.jobs.services import JobService, ApplicationService, CheckInService
from apps.payments.models import Transaction, Escrow, Payout, TransactionStatus, EscrowStatus, PayoutStatus
from apps.users.models import UserType

User = get_user_model()

def run_verification():
    print("🚀 Starting Payment Flow Verification...")
    
    # 1. Create Users
    print("\n1. Creating Users...")
    try:
        business = User.objects.get(phone='+996555000111')
        business.delete()
        print("   (Deleted existing business user)")
    except User.DoesNotExist:
        pass

    try:
        worker = User.objects.get(phone='+996555000222')
        worker.delete()
        print("   (Deleted existing worker user)")
    except User.DoesNotExist:
        pass

    from apps.users.models import BusinessProfile, WorkerProfile

    business = User.objects.create_user(
        phone='+996555000111',
        password='password123',
        user_type=UserType.BUSINESS
    )
    BusinessProfile.objects.create(user=business, company_name="Test Company")
    print(f"✅ Business created: {business.phone}")

    worker = User.objects.create_user(
        phone='+996555000222',
        password='password123',
        user_type=UserType.WORKER
    )
    WorkerProfile.objects.create(
        user=worker,
        full_name="Test Worker",
        verification_status='verified',
        payment_account_id="acct_test_123"
    )
    print(f"✅ Worker created: {worker.phone}")

    # 2. Create & Publish Job
    print("\n2. Creating and Publishing Job...")
    job = Job.objects.create(
        business=business,
        title="Urgent Loader Needed",
        description="Load boxes",
        job_type=JobType.LOADER,
        date=timezone.now().date() + timedelta(days=1),
        start_time=timezone.now().time(),
        end_time=(timezone.now() + timedelta(hours=5)).time(),
        hourly_rate=Decimal('500.00'),  # 500 som/hour
        workers_needed=1,
        location_lat=42.8746,
        location_lng=74.5698,
        location_address="Bishkek Park",
        location_name="Shopping Mall"
    )
    
    JobService.publish_job(job, business)
    print(f"✅ Job published: {job.title} ({job.hourly_rate}/hr)")

    # 3. Apply for Job
    print("\n3. Worker Applying...")
    application = ApplicationService.apply_to_job(job, worker, "I am strong!")
    print(f"✅ Application created: ID {application.id}")

    # 4. Accept Application (Should trigger Escrow)
    print("\n4. Accepting Application (Triggering Escrow)...")
    ApplicationService.accept_application(application, business)
    print(f"✅ Application accepted")

    # Verify Escrow
    transaction = Transaction.objects.get(job=job)
    escrow = Escrow.objects.get(transaction=transaction)
    print(f"💰 Escrow Created: {escrow.held_amount} KGS (Status: {escrow.status})")
    print(f"   Transaction Status: {transaction.status}")
    print(f"   Platform Fee: {transaction.platform_fee}")
    print(f"   Worker Payout (Estimated): {transaction.worker_payout}")

    assert escrow.status == EscrowStatus.HELD
    assert transaction.status == TransactionStatus.PENDING

    # 5. Check-in
    print("\n5. Worker Checking In...")
    # Mock location matching job location
    CheckInService.check_in(
        application, 
        lat=42.8746, 
        lng=74.5698
    )
    print(f"✅ Checked in at {timezone.now()}")

    # Simulate working for 2 hours (modify check-in time manually)
    checkin = application.checkin
    checkin.checked_in_at = timezone.now() - timedelta(hours=2)
    checkin.save()
    print("   (Simulated 2 hours of work)")

    # 6. Check-out (Should release Escrow & Create Payout)
    print("\n6. Worker Checking Out (Triggering Release)...")
    payout_checkin = CheckInService.check_out(
        checkin,
        lat=42.8746, 
        lng=74.5698
    )
    
    # Verify Release
    transaction.refresh_from_db()
    escrow.refresh_from_db()
    
    print(f"✅ Checked out. Worked hours: {payout_checkin.worked_hours}")
    print(f"💰 Escrow Status: {escrow.status}")
    print(f"   Transaction Status: {transaction.status}")
    print(f"   Final Amount: {transaction.amount}")
    
    # Verify Payout
    payout = Payout.objects.get(transaction=transaction)
    print(f"💸 Payout Created: {payout.amount} KGS to {payout.worker.phone}")
    print(f"   Payout Status: {payout.status}")

    assert escrow.status == EscrowStatus.RELEASED
    assert transaction.status == TransactionStatus.HELD
    assert payout.status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]  # Mock PSP usually returns Success/Processing

    print("\n✨ VERIFICATION SUCCESSFUL! Payment flow works correctly.")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
