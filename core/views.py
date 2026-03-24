import PyPDF2
from django.shortcuts import render, redirect
from .forms import ParentForm, MedicalReportForm
from django.contrib.auth.models import User  # add this at top
from .models import Parent, MedicalReport
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .forms import MedicineForm
from .models import Medicine
import datetime
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
import datetime
from django.core.mail import send_mail
from .forms import AppointmentForm
from .models import Appointment
import datetime
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

def delete_appointment(request, id):
    app = get_object_or_404(Appointment, id=id)
    app.delete()
    return redirect('home')

def check_appointment_reminders(request):
    now = datetime.datetime.now()

    appointments = Appointment.objects.filter(parent__user=request.user)

    for app in appointments:
        if app.date == now.date() and app.time.hour == now.hour and app.time.minute == now.minute:
            send_mail(
                '📅 Appointment Reminder',
                f'Appointment with Dr. {app.doctor_name} for {app.parent.name} at {app.time}',
                'your_email@gmail.com',
                ['your_real_email@gmail.com'],
                fail_silently=False,
            )

def add_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)

            appointment.parent = Parent.objects.get(
                id=request.POST.get('parent'),
                user=request.user
            )

            appointment.save()
            return redirect('home')
    else:
        form = AppointmentForm()

    # ✅ ALWAYS RETURN THIS
    return render(request, 'add_appointment.html', {'form': form})

def check_missed_medicines():
    now = datetime.datetime.now().time()

    medicines = Medicine.objects.filter(taken=False)

    for med in medicines:
        if med.time < now:   # ⏰ time passed
            send_mail(
    '⚠️ Missed Medicine Alert',
    f'You missed {med.name} for {med.parent.name}',
    'mrvarshit001@gmail.com',   # sender
    ['mrvarshit001@gmail.com'], # receiver ✅
)
def mark_taken(request, id):
    med = get_object_or_404(Medicine, id=id)
    med.taken = True
    med.save()
    return redirect('home')
def check_medicine_reminders():
    now = datetime.datetime.now().time()

    medicines = Medicine.objects.all()

    for med in medicines:
        # check if time matches (minute-level)
        if med.time.hour == now.hour and med.time.minute == now.minute:
            send_mail(
                '💊 Medicine Reminder',
                f'Time to take {med.name} for {med.parent.name}',
                'your_email@gmail.com',
                ['your_real_email@gmail.com'],
                fail_silently=False,
            )
@login_required
def emergency_alert(request):
    send_mail(
        '🚨 Emergency Alert',
        'Your parent may need immediate assistance!',
        'your_email@gmail.com',
        ['mrvarshit001@gmail.com'],  # put your email here
        fail_silently=False,
    )
    return redirect('home')
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})
def edit_parent(request, id):
    parent = get_object_or_404(Parent, id=id)

    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ParentForm(instance=parent)

    return render(request, 'edit_parent.html', {'form': form})

from django.db.models import Count

from django.db.models import Count

def home(request):
    parents = None
    medicines = None
    appointments = None
    labels = []
    data = []
    medicine_compliance_data = [0, 0]
    app_labels = []
    app_counts = []
    reports = None

    if request.user.is_authenticated:
        parents = Parent.objects.filter(user=request.user)
        medicines = Medicine.objects.filter(parent__user=request.user)
        appointments = Appointment.objects.filter(parent__user=request.user)
        reports = MedicalReport.objects.filter(parent__user=request.user)

        check_missed_medicines()
        check_appointment_reminders(request)

        # 1. Medicines per Parent
        chart_data = (
            medicines
            .values('parent__name')
            .annotate(count=Count('id'))
        )
        labels = [item['parent__name'] for item in chart_data]
        data = [item['count'] for item in chart_data]

        # 2. Medicine Compliance (Taken vs Pending)
        taken_count = medicines.filter(taken=True).count()
        pending_count = medicines.filter(taken=False).count()
        medicine_compliance_data = [taken_count, pending_count]

        # 3. Appointments per Parent
        app_data = (
            appointments
            .values('parent__name')
            .annotate(count=Count('id'))
        )
        app_labels = [item['parent__name'] for item in app_data]
        app_counts = [item['count'] for item in app_data]

    return render(request, 'home.html', {
        'parents': parents,
        'medicines': medicines,
        'appointments': appointments,
        'reports': reports,
        'labels': labels,
        'data': data,
        'compliance_data': medicine_compliance_data,
        'app_labels': app_labels,
        'app_counts': app_counts
    })

def analyze_pdf_report(file_obj):
    try:
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        text = text.lower()
        warnings = []
        
        if 'hemoglobin' in text and 'low' in text:
            warnings.append('Hemoglobin low ⚠️')
        if 'sugar' in text and 'high' in text:
            warnings.append('Sugar high ⚠️')
        if 'glucose' in text and 'high' in text:
            warnings.append('Glucose high ⚠️')
        if 'pressure' in text and 'high' in text:
            warnings.append('Blood Pressure high ⚠️')
        if 'cholesterol' in text and 'high' in text:
            warnings.append('Cholesterol high ⚠️')

        if warnings:
            return " | ".join(warnings)
        return "No critical anomalies found."
    except Exception as e:
        return "Could not auto-analyze."

@login_required
def add_report(request):
    if request.method == 'POST':
        form = MedicalReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            if report.parent.user == request.user:
                if report.file.name.lower().endswith('.pdf'):
                    report.analysis = analyze_pdf_report(request.FILES['file'])
                else:
                    report.analysis = "Analysis requires a PDF file."
                    
                report.save()
                return redirect('home')
    else:
        # Pre-filter parent queryset
        form = MedicalReportForm()
        form.fields['parent'].queryset = Parent.objects.filter(user=request.user)

    return render(request, 'add_report.html', {'form': form})

@login_required
def delete_report(request, id):
    report = get_object_or_404(MedicalReport, id=id)
    report.delete()
    return redirect('home')
@login_required
def add_parent(request):
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.user = request.user   # connect to logged-in user
            parent.save()
            return redirect('home')
    else:
        form = ParentForm()

    return render(request, 'add_parent.html', {'form': form})

def delete_parent(request, id):
    parent = get_object_or_404(Parent, id=id)
    parent.delete()
    return redirect('home')
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = MedicineForm()

    return render(request, 'add_medicine.html', {'form': form})