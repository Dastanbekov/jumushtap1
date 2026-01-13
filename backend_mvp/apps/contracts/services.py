import os
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Contract

def generate_contract(deal):
    # Try importing WeasyPrint, handle failure gracefully for MVP on Windows without GTK3
    try:
        from weasyprint import HTML
        USE_WEASYPRINT = True
    except (ImportError, OSError):
        USE_WEASYPRINT = False

    context = {
        'deal': deal,
        'customer': deal.customer,
        'worker': deal.worker,
        'order': deal.order,
        'date': timezone.now()
    }
    
    html_string = render_to_string('contracts/contract_template.html', context)
    
    if USE_WEASYPRINT:
        try:
            pdf_file = HTML(string=html_string).write_pdf()
            content = ContentFile(pdf_file)
        except Exception as e:
            # Fallback if WeasyPrint fails independently of import
            content = ContentFile(b"%PDF-1.4 ... (WeasyPrint failed, dummy content) ...")
    else:
        # Fallback if import failed
        content = ContentFile(b"%PDF-1.4 ... (WeasyPrint not installed/configured) ...")
    
    contract = Contract.objects.create(deal=deal)
    contract.file.save(f'contract_{deal.id}.pdf', content)
    return contract
