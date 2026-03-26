from django.contrib import admin
from .models import Parent, Medicine, Appointment, MedicalReport, VitalLog, EmailOTP, AuditLog

admin.site.register(Parent)
admin.site.register(Medicine)
admin.site.register(Appointment)
admin.site.register(MedicalReport)
admin.site.register(VitalLog)
admin.site.register(EmailOTP)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('created_at', 'actor', 'action', 'entity_type', 'entity_id')
	list_filter = ('action', 'entity_type', 'created_at')
	search_fields = ('actor__username', 'action', 'entity_type', 'entity_id', 'details')
