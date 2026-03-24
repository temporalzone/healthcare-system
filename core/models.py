from django.db import models
from django.contrib.auth.models import User

class Parent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    health_condition = models.TextField()
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Medicine(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    time = models.TimeField()
    taken = models.BooleanField(default=False)   # ✅ NEW FIELD

    def __str__(self):
        return self.name
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