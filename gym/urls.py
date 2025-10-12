from django.urls import path
from . import views

urlpatterns = [
    path('register-gym/', views.register_gym_form, name='register_gym_form'),
    path('allocate-card/', views.allocate_card_to_gym_page, name='allocate_card_to_gym_page'),
    path('card-count/', views.gym_card_count, name='gym_card_count'),
    path('manage-cards/', views.manage_gym_cards, name='manage_gym_cards'),
    path('deallocate-nfc/', views.deallocate_gym_nfc, name='deallocate_gym_nfc'),
    path('manage-gyms/', views.manage_gyms, name='manage_gyms'),
    path('toggle-gym-approval/<str:gym_id>/', views.toggle_gym_approval, name='toggle_gym_approval'),
    path('gym-dashboard/<str:gym_id>/', views.gym_dashboard, name='gym_dashboard'),
]
