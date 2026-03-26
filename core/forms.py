from django import forms
from .models import Parent
from .models import Medicine
from .models import Appointment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['name', 'age', 'health_condition', 'city', 'emergency_contact_email']


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6, label='OTP')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already registered.')
        return email

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

from .models import VitalLog

class VitalLogForm(forms.ModelForm):
    class Meta:
        model = VitalLog
        fields = ['parent', 'date', 'time', 'bp_sys', 'bp_dia', 'sugar', 'pulse', 'spo2', 'weight']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'bp_sys': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'bp_dia': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'sugar': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'pulse': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'spo2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
        }