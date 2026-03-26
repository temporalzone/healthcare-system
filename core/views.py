import PyPDF2
import json
import datetime
import random
import string
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.utils import timezone

from .forms import (
    AppointmentForm,
    MedicalReportForm,
    MedicineForm,
    OTPVerificationForm,
    ParentForm,
    RegisterForm,
    UserProfileForm,
    VitalLogForm,
)
from .models import Appointment, AuditLog, EmailOTP, MedicalReport, Medicine, MedicineLog, Parent, VitalLog

MAX_OTP_ATTEMPTS = 5
OTP_LOCKOUT_MINUTES = 15
OTP_RESEND_COOLDOWN_SECONDS = 30


def _log_audit(request, action, entity_type, entity_id='', details=''):
    AuditLog.objects.create(
        actor=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else '',
        details=details,
    )


def _allowed_parents_queryset(user):
    if hasattr(user, 'parent_profile'):
        return Parent.objects.filter(id=user.parent_profile.id)
    return Parent.objects.filter(user=user)


def _generate_otp():
    return ''.join(random.choice(string.digits) for _ in range(6))


def _send_registration_otp(user):
    otp_code = _generate_otp()
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            'code': otp_code,
            'expires_at': timezone.now() + datetime.timedelta(minutes=10),
            'resend_available_at': timezone.now() + datetime.timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS),
            'verified': False,
            'failed_attempts': 0,
            'locked_until': None,
        },
    )

    send_mail(
        'Verify your CareBridge account',
        f'Your OTP is {otp_code}. It will expire in 10 minutes.',
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )


def _cleanup_stale_unverified_users(username, email):
    stale_users = User.objects.filter(is_active=False).filter(username=username) | User.objects.filter(is_active=False).filter(email__iexact=email)
    for stale_user in stale_users.distinct():
        otp = EmailOTP.objects.filter(user=stale_user, verified=False).first()
        if otp:
            stale_user.delete()

@login_required
def delete_appointment(request, id):
    app = get_object_or_404(Appointment, id=id, parent__in=_allowed_parents_queryset(request.user))
    _log_audit(request, 'delete_appointment', 'Appointment', app.id, f'Doctor: {app.doctor_name}')
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

@login_required
def add_appointment(request):
    allowed_parents = _allowed_parents_queryset(request.user)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        form.fields['parent'].queryset = allowed_parents
        if form.is_valid():
            appointment = form.save()
            _log_audit(request, 'add_appointment', 'Appointment', appointment.id, f'Doctor: {appointment.doctor_name}')
            return redirect('home')
    else:
        form = AppointmentForm()
        form.fields['parent'].queryset = allowed_parents

    # ✅ ALWAYS RETURN THIS
    return render(request, 'add_appointment.html', {'form': form})

def check_missed_medicines():
    now = datetime.datetime.now()
    today = now.date()
    current_time = now.time()

    logs = MedicineLog.objects.filter(date=today, taken=False)

    for log in logs:
        med = log.medicine
        if med.time < current_time:   # ⏰ time passed
            send_mail(
                '⚠️ Missed Medicine Alert',
                f'You missed {med.name} for {med.parent.name}',
                'mrvarshit001@gmail.com',   # sender
                ['mrvarshit001@gmail.com'], # receiver ✅
            )
@login_required
def mark_taken(request, log_id):
    log = get_object_or_404(MedicineLog, id=log_id, medicine__parent__in=_allowed_parents_queryset(request.user))
    now = datetime.datetime.now()
    
    if log.date > now.date():
        from django.contrib import messages
        messages.error(request, "You cannot mark a medicine taken in the future date!")
        return redirect(f"/?date={log.date.isoformat()}")
        
    if log.date == now.date() and log.medicine.time > now.time():
        from django.contrib import messages
        messages.error(request, f"It is not time yet to take {log.medicine.name} (Scheduled parameter time: {log.medicine.time.strftime('%I:%M %p')}).")
        return redirect(f"/?date={log.date.isoformat()}")

    log.taken = True
    log.save()
    _log_audit(request, 'mark_medicine_taken', 'MedicineLog', log.id, f'Medicine: {log.medicine.name}, Date: {log.date}')
    return redirect(f"/?date={log.date.isoformat()}")
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
        posted_username = request.POST.get('username', '').strip()
        posted_email = request.POST.get('email', '').strip().lower()
        if posted_username or posted_email:
            _cleanup_stale_unverified_users(posted_username, posted_email)

        form = RegisterForm(request.POST)
        role = request.POST.get('role', 'caregiver')
        invite_code = request.POST.get('invite_code', '').strip().upper()

        if role == 'patient':
            if not invite_code:
                messages.error(request, "Invite code is required for patients.")
                return render(request, 'register.html', {'form': form})

            try:
                parent = Parent.objects.get(invite_code=invite_code)
                if parent.patient_account:
                    messages.error(request, "This invite code has already been used.")
                    return render(request, 'register.html', {'form': form})
            except Parent.DoesNotExist:
                messages.error(request, "Invalid invite code.")
                return render(request, 'register.html', {'form': form})

        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.is_active = False
            user.save()
            _log_audit(request, 'register_pending', 'User', user.id, f'Role: {role}, Email: {user.email}')

            request.session['pending_user_id'] = user.id
            request.session['pending_role'] = role
            request.session['pending_invite_code'] = invite_code

            try:
                _send_registration_otp(user)
                _log_audit(request, 'otp_sent', 'User', user.id, 'Registration OTP sent')
            except Exception:
                user.delete()
                request.session.pop('pending_user_id', None)
                request.session.pop('pending_role', None)
                request.session.pop('pending_invite_code', None)
                messages.error(request, 'Could not send OTP to this email. Please check the email address and try again.')
                return render(request, 'register.html', {'form': form})

            messages.success(request, f"We sent an OTP to {user.email}. Enter it to verify your account.")
            return redirect('verify_email')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def verify_email(request):
    pending_user_id = request.session.get('pending_user_id')
    if not pending_user_id:
        messages.error(request, 'No pending registration found. Please register first.')
        return redirect('register')

    user = get_object_or_404(User, id=pending_user_id)
    otp_record = EmailOTP.objects.filter(user=user).first()

    if not otp_record:
        messages.error(request, 'No OTP found. Please register again.')
        return redirect('register')

    form = OTPVerificationForm(request.POST or None)

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')

        if action == 'resend':
            now = timezone.now()
            if otp_record.resend_available_at and now < otp_record.resend_available_at:
                wait_seconds = int((otp_record.resend_available_at - now).total_seconds())
                messages.error(request, f'Please wait {wait_seconds} second(s) before requesting a new OTP.')
                return redirect('verify_email')
            _send_registration_otp(user)
            _log_audit(request, 'otp_resent', 'User', user.id, 'Registration OTP resent')
            messages.success(request, f'A new OTP was sent to {user.email}.')
            return redirect('verify_email')

        if form.is_valid():
            entered_otp = form.cleaned_data['otp'].strip()
            otp_record.refresh_from_db()

            if otp_record.is_locked():
                wait_seconds = int((otp_record.locked_until - timezone.now()).total_seconds())
                wait_minutes = max(1, (wait_seconds + 59) // 60)
                messages.error(request, f'Too many invalid attempts. Try again in {wait_minutes} minute(s).')
            elif otp_record.is_expired():
                messages.error(request, 'OTP expired. Please click resend OTP.')
            elif entered_otp != otp_record.code:
                otp_record.failed_attempts += 1
                if otp_record.failed_attempts >= MAX_OTP_ATTEMPTS:
                    otp_record.locked_until = timezone.now() + datetime.timedelta(minutes=OTP_LOCKOUT_MINUTES)
                    otp_record.failed_attempts = 0
                    otp_record.save(update_fields=['failed_attempts', 'locked_until'])
                    messages.error(request, f'Too many invalid attempts. OTP verification is locked for {OTP_LOCKOUT_MINUTES} minutes.')
                else:
                    otp_record.save(update_fields=['failed_attempts'])
                    attempts_left = MAX_OTP_ATTEMPTS - otp_record.failed_attempts
                    messages.error(request, f'Invalid OTP. {attempts_left} attempt(s) left.')
            else:
                role = request.session.get('pending_role', 'caregiver')
                invite_code = request.session.get('pending_invite_code', '')

                if role == 'patient':
                    try:
                        parent = Parent.objects.get(invite_code=invite_code)
                        if parent.patient_account:
                            messages.error(request, 'Invite code is already used. Contact your caregiver.')
                            return redirect('register')
                        parent.patient_account = user
                        parent.save()
                    except Parent.DoesNotExist:
                        messages.error(request, 'Invite code became invalid. Please register again.')
                        return redirect('register')

                user.is_active = True
                user.save()
                otp_record.verified = True
                otp_record.failed_attempts = 0
                otp_record.locked_until = None
                otp_record.save(update_fields=['verified', 'failed_attempts', 'locked_until'])
                _log_audit(request, 'verify_email_success', 'User', user.id, 'Account activated via OTP')

                request.session.pop('pending_user_id', None)
                request.session.pop('pending_role', None)
                request.session.pop('pending_invite_code', None)

                messages.success(request, 'Email verified successfully. Please log in.')
                return redirect('login')

    return render(request, 'verify_email.html', {
        'form': form,
        'email': user.email,
        'otp_expires_at': int(otp_record.expires_at.timestamp()) if otp_record.expires_at else None,
        'resend_available_at': int(otp_record.resend_available_at.timestamp()) if otp_record.resend_available_at else None,
    })
@login_required
def edit_parent(request, id):
    parent = get_object_or_404(Parent, Q(user=request.user) | Q(patient_account=request.user), id=id)

    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            parent = form.save()
            _log_audit(request, 'edit_parent', 'Parent', parent.id, f'Updated parent profile for {parent.name}')
            return redirect('home')
    else:
        form = ParentForm(instance=parent)

    return render(request, 'edit_parent.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            _log_audit(request, 'edit_profile', 'User', user.id, 'Updated account profile details')
            messages.success(request, 'Profile updated successfully.')
            return redirect('home')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})

def home(request):
    parents = None
    medicines = None
    appointments = None
    labels = []
    data = []
    medicine_compliance_data = [0, 0]
    reports = None
    selected_date_str = ""
    today_str = datetime.date.today().isoformat()
    
    vitals_dates = []
    vitals_bp_sys = []
    vitals_bp_dia = []
    vitals_sugar = []

    is_patient_dashboard = False
    is_sunday_vitals_reminder = False
    unlogged_parents_str = ""

    if request.user.is_authenticated:
        is_patient_dashboard = hasattr(request.user, 'parent_profile')
        date_str = request.GET.get('date')
        if date_str:
            try:
                today = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                today = datetime.date.today()
        else:
            today = datetime.date.today()
            
        selected_date_str = today.isoformat()

        if is_patient_dashboard:
            parents = Parent.objects.filter(id=request.user.parent_profile.id)
            medicines = Medicine.objects.filter(parent__in=parents)
        else:
            parents = Parent.objects.filter(user=request.user)
            medicines = Medicine.objects.filter(parent__user=request.user)
        
        for parent in parents:
            parent.latest_vitals = VitalLog.objects.filter(parent=parent).order_by('-date', '-time').first()
            if not is_patient_dashboard and not parent.invite_code:
                parent.invite_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                parent.save()

        if parents.exists():
            primary_parent = parents.first()
            weekly_grouped = {}
            for v in VitalLog.objects.filter(parent=primary_parent).order_by('date', 'time'):
                year, week, _ = v.date.isocalendar()
                key = (year, week)
                if key not in weekly_grouped:
                    weekly_grouped[key] = {
                        'date_label': f"Wk {week}, {year}",
                        'bp_sys': [], 'bp_dia': [], 'sugar': []
                    }
                if v.bp_sys: weekly_grouped[key]['bp_sys'].append(v.bp_sys)
                if v.bp_dia: weekly_grouped[key]['bp_dia'].append(v.bp_dia)
                if v.sugar: weekly_grouped[key]['sugar'].append(v.sugar)
            
            recent_weeks = list(weekly_grouped.values())[-12:]
            for w in recent_weeks:
                vitals_dates.append(w['date_label'])
                vitals_bp_sys.append(round(sum(w['bp_sys'])/len(w['bp_sys'])) if w['bp_sys'] else None)
                vitals_bp_dia.append(round(sum(w['bp_dia'])/len(w['bp_dia'])) if w['bp_dia'] else None)
                vitals_sugar.append(round(sum(w['sugar'])/len(w['sugar'])) if w['sugar'] else None)

        if today.weekday() == 6: # Sunday
            unlogged = []
            for p in parents:
                if not VitalLog.objects.filter(parent=p, date=today).exists():
                    unlogged.append(p.name)
            if unlogged:
                is_sunday_vitals_reminder = True
                unlogged_parents_str = ", ".join(unlogged)
        
        for med in medicines:
            log, created = MedicineLog.objects.get_or_create(medicine=med, date=today)
            med.today_log = log
            
        if is_patient_dashboard:
            appointments = Appointment.objects.filter(parent__in=parents)
            reports = MedicalReport.objects.filter(parent__in=parents)
        else:
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

        # 2. Medicine Compliance (Taken vs Pending) for selected date
        logs = MedicineLog.objects.filter(medicine__in=medicines, date=today)
        taken_count = logs.filter(taken=True).count()
        pending_count = logs.filter(taken=False).count()
        medicine_compliance_data = [taken_count, pending_count]

    return render(request, 'home.html', {
        'parents': parents,
        'medicines': medicines,
        'appointments': appointments,
        'reports': reports,
        'labels': labels,
        'data': data,
        'compliance_data': medicine_compliance_data,
        'selected_date_str': selected_date_str,
        'today_str': today_str,
        'vitals_dates': json.dumps(vitals_dates),
        'vitals_bp_sys': json.dumps(vitals_bp_sys),
        'vitals_bp_dia': json.dumps(vitals_bp_dia),
        'vitals_sugar': json.dumps(vitals_sugar),
        'is_sunday_vitals_reminder': is_sunday_vitals_reminder,
        'unlogged_parents_str': unlogged_parents_str,
        'is_patient_dashboard': is_patient_dashboard,
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
    allowed_parents = _allowed_parents_queryset(request.user)

    if request.method == 'POST':
        form = MedicalReportForm(request.POST, request.FILES)
        form.fields['parent'].queryset = allowed_parents
        if form.is_valid():
            report = form.save(commit=False)
            is_valid_user = (report.parent.user == request.user) or (hasattr(request.user, 'parent_profile') and report.parent == request.user.parent_profile)
            if is_valid_user:
                if report.file.name.lower().endswith('.pdf'):
                    report.analysis = analyze_pdf_report(request.FILES['file'])
                else:
                    report.analysis = "Analysis requires a PDF file."
                    
                report.save()
                _log_audit(request, 'add_report', 'MedicalReport', report.id, f'Report: {report.name}')
                return redirect('home')
            messages.error(request, 'You are not allowed to upload reports for this profile.')
    else:
        # Pre-filter parent queryset
        form = MedicalReportForm()
        form.fields['parent'].queryset = allowed_parents

    return render(request, 'add_report.html', {'form': form})

@login_required
def sos_alert(request, id):
    if request.method == 'POST':
        try:
            from django.db.models import Q
            parent = get_object_or_404(Parent, Q(user=request.user) | Q(patient_account=request.user), id=id)
            
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            recipients = []
            
            # If the Patient pressed SOS, send the alert to the Caregiver (their child/manager)
            if hasattr(request.user, 'parent_profile') and request.user.parent_profile == parent:
                if parent.user.email:
                    recipients.append(parent.user.email)
            
            # Plus, always send to the explicitly defined emergency contact (Secondary/Doctor)
            if parent.emergency_contact_email:
                recipients.append(parent.emergency_contact_email)
                
            if not recipients:
                return JsonResponse({'status': 'error', 'message': 'No emergency contact emails could be found (neither the Caregiver nor an explicit contact).'})
                
            recipients = list(set(recipients)) # Deduplicate
            
            maps_link = f"https://maps.google.com/?q={lat},{lng}"
            
            # Context
            vitals = VitalLog.objects.filter(parent=parent).order_by('-date', '-time').first()
            meds = MedicineLog.objects.filter(medicine__parent=parent, date=datetime.date.today())
            taken_meds = [m.medicine.name for m in meds if m.taken]
            pending_meds = [m.medicine.name for m in meds if not m.taken]
            
            subject = f"🚨 EMERGENCY SOS: {parent.name} 🚨"
            message = "EMERGENCY ALERT TRIGGERED\n\n"
            message += f"Patient: {parent.name} ({parent.age} yrs)\n"
            message += f"Condition: {parent.health_condition}\n\n"
            message += f"📍 LIVE LOCATION: {maps_link}\n\n"
            
            if vitals:
                message += f"Latest Vitals ({vitals.date}):\n"
                if vitals.bp_sys: message += f"- BP: {vitals.bp_sys}/{vitals.bp_dia}\n"
                if vitals.sugar: message += f"- Sugar: {vitals.sugar}\n"
                if vitals.pulse: message += f"- Pulse: {vitals.pulse}\n"
                if vitals.spo2: message += f"- SpO2: {vitals.spo2}%\n"
            
            message += "\nToday's Medicines:\n"
            message += f"- Taken: {', '.join(taken_meds) if taken_meds else 'None'}\n"
            message += f"- Pending: {', '.join(pending_meds) if pending_meds else 'None'}\n"
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER, # Use the authenticated Gmail address to prevent SMTP rejection
                recipients,
                fail_silently=False,
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@login_required
def delete_report(request, id):
    report = get_object_or_404(MedicalReport, id=id, parent__in=_allowed_parents_queryset(request.user))
    _log_audit(request, 'delete_report', 'MedicalReport', report.id, f'Report: {report.name}')
    report.delete()
    return redirect('home')
@login_required
def add_parent(request):
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.user = request.user   # connect to logged-in user
            
            import string
            import random
            # Generate a 6-character random invite code
            code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            parent.invite_code = code
            
            parent.save()
            _log_audit(request, 'add_parent', 'Parent', parent.id, f'Parent: {parent.name}')
            return redirect('home')
    else:
        form = ParentForm()

    return render(request, 'add_parent.html', {'form': form})

@login_required
def delete_parent(request, id):
    parent = get_object_or_404(Parent, id=id, user=request.user)
    _log_audit(request, 'delete_parent', 'Parent', parent.id, f'Parent: {parent.name}')
    parent.delete()
    return redirect('home')

@login_required
def delete_account(request):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for account deletion.')
        return redirect('home')

    _log_audit(request, 'delete_account', 'User', request.user.id, f'Username: {request.user.username}')
    user = request.user
    user.delete()
    return redirect('login')
@login_required
def add_medicine(request):
    allowed_parents = _allowed_parents_queryset(request.user)

    if request.method == 'POST':
        form = MedicineForm(request.POST)
        form.fields['parent'].queryset = allowed_parents
        if form.is_valid():
            medicine = form.save()
            _log_audit(request, 'add_medicine', 'Medicine', medicine.id, f'Medicine: {medicine.name}')
            return redirect('home')
    else:
        form = MedicineForm()
        form.fields['parent'].queryset = allowed_parents

    return render(request, 'add_medicine.html', {'form': form})

@login_required
def delete_medicine(request, id):
    med = get_object_or_404(Medicine, id=id, parent__in=_allowed_parents_queryset(request.user))
    _log_audit(request, 'delete_medicine', 'Medicine', med.id, f'Medicine: {med.name}')
    med.delete()
    return redirect('home')

@login_required
def add_vital(request):
    allowed_parents = _allowed_parents_queryset(request.user)

    if request.method == 'POST':
        form = VitalLogForm(request.POST)
        form.fields['parent'].queryset = allowed_parents
        if form.is_valid():
            vital = form.save()
            _log_audit(request, 'add_vital', 'VitalLog', vital.id, f'Parent ID: {vital.parent.id}, Date: {vital.date}')
            messages.success(request, 'Vitals logged successfully!')
            return redirect('home')
    else:
        form = VitalLogForm()
        form.fields['parent'].queryset = allowed_parents

    return render(request, 'add_vital.html', {'form': form})

# create_parent_login view removed, using invite codes now

@login_required
def custom_logout(request):
    _log_audit(request, 'logout', 'User', request.user.id, f'Username: {request.user.username}')
    logout(request)
    return redirect('login')