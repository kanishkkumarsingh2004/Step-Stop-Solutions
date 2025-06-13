from django.urls import path
from . import institute_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
   path('apply-vendor/apply-for-vendor/coaching/', institute_view.register_coaching_form, name='register_coaching_form'),
   path('enrollment-coaching/success/', institute_view.enrollment_success, name='enrollment_success_coaching'),
   path('coaching/dashboard/', institute_view.coaching_dashboard, name='coaching_dashboard'),
]