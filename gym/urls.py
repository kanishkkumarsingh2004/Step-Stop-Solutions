from django.urls import path
from . import views

urlpatterns = [
    path('register-gym/', views.register_gym_form, name='register_gym_form'),
    path('registration-success/', views.gym_registration_success, name='gym_registration_success'),
    path('allocate-card/', views.allocate_card_to_gym_page, name='allocate_card_to_gym_page'),
    path('card-count/', views.gym_card_count, name='gym_card_count'),
    path('manage-cards/', views.manage_gym_cards, name='manage_gym_cards'),
    path('deallocate-nfc/', views.deallocate_gym_nfc, name='deallocate_gym_nfc'),
    path('manage-gyms/', views.manage_gyms, name='manage_gyms'),
    path('toggle-gym-approval/<str:gym_id>/', views.toggle_gym_approval, name='toggle_gym_approval'),
    path('update-subscription-dates/', views.update_gym_subscription_dates, name='update_gym_subscription_dates'),
    path('gym-dashboard/<str:gym_id>/', views.gym_dashboard, name='gym_dashboard'),
]
