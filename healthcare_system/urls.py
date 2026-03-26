"""
URL configuration for healthcare_system project.
"""
from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('add-parent/', views.add_parent, name='add_parent'),
    path('edit-parent/<int:id>/', views.edit_parent, name='edit_parent'),
    path('delete-parent/<int:id>/', views.delete_parent, name='delete_parent'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('sos-alert/<int:id>/', views.sos_alert, name='sos_alert'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html', success_url='/password-change/done/'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('emergency/', views.emergency_alert, name='emergency'),
    path('add-medicine/', views.add_medicine, name='add_medicine'),
    path('add-vital/', views.add_vital, name='add_vital'),
    path('delete-medicine/<int:id>/', views.delete_medicine, name='delete_medicine'),
    path('mark-taken/<int:log_id>/', views.mark_taken, name='mark_taken'),
    path('add-appointment/', views.add_appointment, name='add_appointment'),
    path('delete-appointment/<int:id>/', views.delete_appointment, name='delete_appointment'),
    path('add-report/', views.add_report, name='add_report'),
    path('delete-report/<int:id>/', views.delete_report, name='delete_report'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
