from .models import PayoutLog
from decimal import Decimal

def process_payout(deal):
    amount = deal.order.price
    commission_rate = Decimal('0.10') # 10%
    commission = amount * commission_rate
    payout_amount = amount - commission
    
    PayoutLog.objects.create(
        worker=deal.worker,
        deal=deal,
        amount=payout_amount,
        commission=commission,
        status='paid' 
    )
