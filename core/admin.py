from django.contrib import admin
from .models import Parent, Medicine, Appointment

admin.site.register(Parent)
admin.site.register(Medicine)
admin.site.register(Appointment)   # ✅ ADD THIS
