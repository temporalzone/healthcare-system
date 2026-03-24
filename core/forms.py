from django import forms
from .models import Parent
from .models import Medicine
from .models import Appointment

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['name', 'age', 'health_condition', 'city']
class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['parent', 'name', 'time']

from .models import MedicalReport

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['parent', 'doctor_name', 'specialization', 'date', 'time', 'notes']

class MedicalReportForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ['parent', 'name', 'date', 'file', 'notes']