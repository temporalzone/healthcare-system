import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcare_system.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print(f"Testing SMTP with {settings.EMAIL_HOST_USER}...")
try:
    send_mail(
        'Test Subject from VitalSync',
        'This is a diagnostic email payload.',
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER], # send to self to verify delivery
        fail_silently=False,
    )
    print("Successfully dispatched SMTP.")
except Exception as e:
    print(f"FAILED SMTP:")
    import traceback
    traceback.print_exc()
