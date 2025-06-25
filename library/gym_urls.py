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
    path('gyms/<str:gim_uid>/upload-profile-image/', gym_views.upload_gym_profile_image, name='upload_gym_profile_image'),
    path('api/gym/<str:gim_uid>/remove-profile-image/', gym_views.remove_gym_profile_image, name='remove_gym_profile_image'),
    path('gyms/<str:gim_uid>/edit/', gym_views.edit_gym_profile, name='edit_gym_profile'),
    path('gyms/<str:gim_uid>/update-upi/', gym_views.update_gym_upi_details, name='update_gym_upi_details'),
]