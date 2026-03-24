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
    path('add-parent/', views.add_parent, name='add_parent'),
    path('edit-parent/<int:id>/', views.edit_parent, name='edit_parent'),
    path('delete-parent/<int:id>/', views.delete_parent, name='delete_parent'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('emergency/', views.emergency_alert, name='emergency'),
    path('add-medicine/', views.add_medicine, name='add_medicine'),
    path('mark-taken/<int:id>/', views.mark_taken, name='mark_taken'),
    path('add-appointment/', views.add_appointment, name='add_appointment'),
    path('delete-appointment/<int:id>/', views.delete_appointment, name='delete_appointment'),
    path('add-report/', views.add_report, name='add_report'),
    path('delete-report/<int:id>/', views.delete_report, name='delete_report'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
