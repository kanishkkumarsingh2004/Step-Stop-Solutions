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
    path('gyms/<str:gim_uid>/check-gym-nfc-allocation/', gym_views.check_gym_nfc_allocation, name='check_gym_nfc_allocation'),
    path('gyms/<str:gim_uid>/allocate-gym-nfc/', gym_views.allocate_gym_nfc, name='allocate_gym_nfc'),
    path('gyms/<str:gim_uid>/deallocate-gym-nfc/', gym_views.deallocate_gym_nfc, name='deallocate_gym_nfc'),
    path('gyms/<str:gim_uid>/ajax-allocate-card/', gym_views.ajax_allocate_gym_card, name='ajax_allocate_gym_card'),
    path('gyms/<str:gim_uid>/expenses/', gym_views.gym_expense_dashboard, name='gym_expense_dashboard'),
    path('gyms/<str:gim_uid>/add-expense/', gym_views.add_gym_expense, name='add_gym_expense'),
    path('gyms/<str:gim_uid>/balance-sheet/', gym_views.gym_balance_sheet, name='gym_balance_sheet'),
    path('gyms/<str:gim_uid>/analytics/', gym_views.gym_analytics_page, name='gym_analytics'),
]