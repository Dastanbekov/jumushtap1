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
from apps.notifications.models import Notification, Device
from apps.notifications.services import NotificationService
from apps.users.models import UserType, BusinessProfile, WorkerProfile

User = get_user_model()

def run_verification():
    print("🚀 Starting Notification Verification...")
    
    # 1. Create Users & Register Devices
    print("\n1. Creating Users & Devices...")
    
    # Cleanup
    User.objects.filter(phone__in=['+996555999001', '+996555999002']).delete()
    
    business = User.objects.create_user(
        phone='+996555999001',
        password='password123',
        user_type=UserType.BUSINESS
    )
    BusinessProfile.objects.create(
        user=business, 
        company_name="Notif Corp",
        bin="BIN123456789",
        inn="INN123456789",
        legal_address="Test Address",
        contact_name="Test Contact",
        contact_number="+996555999001"
    )
    
    worker = User.objects.create_user(
        phone='+996555999002',
        password='password123',
        user_type=UserType.WORKER
    )
    WorkerProfile.objects.create(
        user=worker, 
        full_name="Notif Worker",
        verification_status='verified'
    )
    
    # Register Devices
    NotificationService.register_device(business, "token_business_123", "web")
    NotificationService.register_device(worker, "token_worker_456", "android")
    
    print(f"✅ Devices registered for {business.phone} and {worker.phone}")
    assert Device.objects.count() >= 2

    # 2. Publish Job
    print("\n2. Publishing Job...")
    job = Job.objects.create(
        business=business,
        title="Notify Job",
        description="Testing notifs",
        job_type=JobType.OTHER,
        date=timezone.now().date() + timedelta(days=1),
        start_time=timezone.now().time(),
        end_time=(timezone.now() + timedelta(hours=2)).time(),
        hourly_rate=Decimal('200.00'),
        workers_needed=1,
        location_lat=42.87,
        location_lng=74.56,
        location_address="Test Addr",
        location_name="Test Loc"
    )
    JobService.publish_job(job, business)
    
    # 3. Apply -> Should notify Business
    print("\n3. Worker Applying (Should notify Business)...")
    application = ApplicationService.apply_to_job(job, worker)
    
    # Verify notification for Business
    notif = Notification.objects.filter(
        user=business, 
        data__type='application_received'
    ).last()
    
    assert notif is not None
    print(f"✅ Business received notification: {notif.title} - {notif.body}")
    assert "Notif Worker applied" in notif.body

    # 4. Accept -> Should notify Worker
    print("\n4. Accepting Application (Should notify Worker)...")
    ApplicationService.accept_application(application, business)
    
    # Verify notification for Worker
    notif = Notification.objects.filter(
        user=worker,
        data__type='application_accepted'
    ).last()
    
    assert notif is not None
    print(f"✅ Worker received notification: {notif.title} - {notif.body}")
    assert "accepted" in notif.body

    # 5. Check-in -> Should notify Business
    print("\n5. Check-in (Should notify Business)...")
    checkin = CheckInService.check_in(application, lat=42.87, lng=74.56)
    
    notif = Notification.objects.filter(
        user=business,
        data__type='worker_checkin'
    ).last()
    
    assert notif is not None
    print(f"✅ Business received check-in notification: {notif.title}")
    
    # 6. Check-out -> Should notify Business & Payment Payout (Notify Worker)
    print("\n6. Check-out (Should notify Business & Worker)...")
    
    # Set checkin time back clearly
    checkin.checked_in_at = timezone.now() - timedelta(hours=1)
    checkin.save()
    
    CheckInService.check_out(checkin, lat=42.87, lng=74.56)
    
    # Check Business Notif (Checkout)
    notif_biz = Notification.objects.filter(
        user=business,
        data__type='worker_checkout'
    ).last()
    assert notif_biz is not None
    print(f"✅ Business received checkout notification: {notif_biz.title}")
    
    # Check Worker Notif (Payment)
    notif_worker = Notification.objects.filter(
        user=worker,
        data__type='payment_released'
    ).last()
    
    assert notif_worker is not None
    print(f"✅ Worker received payment notification: {notif_worker.title} - {notif_worker.body}")

    print("\n✨ ALL NOTIFICATIONS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
