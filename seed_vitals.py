import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\mrvar\healthcare_system')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcare_system.settings")
django.setup()

from core.models import Parent, VitalLog
import datetime
import random

parent = Parent.objects.first()
if parent:
    print(f"Seeding data for parent: {parent.name}")
    for i in range(6, 0, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        # Check if log already exists
        if not VitalLog.objects.filter(parent=parent, date=date).exists():
            v = VitalLog.objects.create(
                parent=parent,
                date=date,
                time=datetime.time(10, 0),
                bp_sys=random.randint(115, 130),
                bp_dia=random.randint(75, 88),
                sugar=random.randint(90, 140) if i % 2 == 0 else random.randint(110, 160),
                pulse=random.randint(70, 85),
                spo2=random.randint(95, 99),
                weight=70.5 + (random.random() * 2 - 1)
            )
            print(f"Created log for {date}: {v.bp_sys}/{v.bp_dia} BP")
    print("Done seeding.")
else:
    print("No parent found to seed data for.")
