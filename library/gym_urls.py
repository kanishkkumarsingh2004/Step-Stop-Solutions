from django.urls import path
from . import institute_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import gym_views  

urlpatterns = [
    path('gyms/', gym_views.search_gyms, name='search_gyms'),
    path('gyms/register/', gym_views.register_gym, name='register_gym'),
    path('gyms/register/success/', gym_views.gym_registration_success, name='gym_registration_success'),
    path('gyms/<str:gim_uid>/coupons/', gym_views.manage_gym_coupons, name='manage_gym_coupons'),
    path('gyms/<str:gim_uid>/', gym_views.gym_details, name='gym_details'),
    path('gyms/<str:gim_uid>/dashboard/', gym_views.gym_dashboard, name='gym_dashboard'),
    path('gyms/<str:gim_uid>/upload-profile-image/', gym_views.upload_gym_profile_image, name='upload_gym_profile_image'),
    path('api/gym/<str:gim_uid>/remove-profile-image/', gym_views.remove_gym_profile_image, name='remove_gym_profile_image'),
    path('gyms/<str:gim_uid>/edit/', gym_views.edit_gym_profile, name='edit_gym_profile'),
    path('gyms/<str:gim_uid>/update-upi/', gym_views.update_gym_upi_details, name='update_gym_upi_details'),
    path('gyms/<str:gim_uid>/banners/', gym_views.manage_gym_banners, name='manage_gym_banners'),
    path('gyms/<str:gim_uid>/remove-banner/', gym_views.remove_gym_banner, name='remove_gym_banner'),
    path('gyms/<str:gim_uid>/subscription-plans/', gym_views.manage_gym_subscription_plans, name='manage_gym_subscription_plans'),
    path('gyms/<str:gim_uid>/plans/', gym_views.public_gym_subscription_plans, name='public_gym_subscription_plans'),
    path('gyms/<str:gim_uid>/apply-coupon/', gym_views.ajax_apply_gym_coupon, name='ajax_apply_gym_coupon'),
    path('gyms/<str:gim_uid>/plans/<int:plan_id>/payment/', gym_views.public_gym_subscription_payment, name='public_gym_subscription_payment'),
    path('gyms/<str:gim_uid>/plans/<int:plan_id>/payment/success/', gym_views.public_gym_subscription_success, name='public_gym_subscription_success'),
    path('gyms/<str:gim_uid>/verify-payments/', gym_views.gym_verify_payments, name='gym_verify_payments'),
    path('gyms/<str:gim_uid>/enrolled-users/', gym_views.manage_gym_enrolled_users, name='manage_gym_enrolled_users'),
    path('gyms/<str:gim_uid>/allocate-card/', gym_views.allocate_gym_card_page, name='allocate_gym_card_page'),
    path('gyms/<str:gim_uid>/ajax-allocate-card/', gym_views.ajax_allocate_gym_card, name='ajax_allocate_gym_card'),
]