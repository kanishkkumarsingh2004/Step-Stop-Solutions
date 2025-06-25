from django.urls import path
from . import institute_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import gym_views  

urlpatterns = [
    path('gyms/', gym_views.search_gyms, name='search_gyms'),
    path('gyms/register/', gym_views.register_gym, name='register_gym'),
    path('gyms/register/success/', gym_views.gym_registration_success, name='gym_registration_success'),
    path('gyms/<str:gim_uid>/', gym_views.gym_details, name='gym_details'),
    path('gyms/<str:gim_uid>/dashboard/', gym_views.gym_dashboard, name='gym_dashboard'),
]