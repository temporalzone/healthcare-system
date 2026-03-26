from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Parent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_account = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_profile')
    invite_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    health_condition = models.TextField()
    city = models.CharField(max_length=100)
    emergency_contact_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name
class Medicine(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    time = models.TimeField()

    def __str__(self):
        return self.name

class MedicineLog(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    taken = models.BooleanField(default=False)

    class Meta:
        unique_together = ('medicine', 'date')
        ordering = ['-date']
class Appointment(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    doctor_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.doctor_name} - {self.parent.name}"

class MedicalReport(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date = models.DateField()
    file = models.FileField(upload_to='reports/')
    notes = models.TextField(blank=True)
    analysis = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.parent.name}"

class VitalLog(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='vitals')
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    bp_sys = models.IntegerField(null=True, blank=True, help_text="Systolic BP (e.g. 120)")
    bp_dia = models.IntegerField(null=True, blank=True, help_text="Diastolic BP (e.g. 80)")
    sugar = models.IntegerField(null=True, blank=True, help_text="Blood Sugar mg/dL")
    pulse = models.IntegerField(null=True, blank=True, help_text="Heart Rate bpm")
    spo2 = models.IntegerField(null=True, blank=True, help_text="Blood Oxygen %")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"Vitals for {self.parent.name} on {self.date}"


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    resend_available_at = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_locked(self):
        return self.locked_until is not None and timezone.now() < self.locked_until

    def __str__(self):
        return f"OTP for {self.user.username}"


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=50, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.entity_type} ({self.entity_id})"