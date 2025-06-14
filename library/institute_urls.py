from django.urls import path
from . import institute_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
   path('apply-vendor/apply-for-vendor/coaching/', institute_view.register_coaching_form, name='register_coaching_form'),
   path('enrollment-coaching/success/', institute_view.enrollment_success, name='enrollment_success_coaching'),
   path('coaching/dashboard/<str:uid>/', institute_view.coaching_dashboard, name='coaching_dashboard'),
   path('institution/<str:uid>/', institute_view.institution_details, name='institution_details'),
   path('institution/<str:uid>/approve/', institute_view.approve_institution, name='approve_institution'),
   path('institution/<str:uid>/unapprove/', institute_view.unapprove_institution, name='unapprove_institution'),
   path('institute-details/<str:uid>/', institute_view.public_institute_details, name='public_institute_details'),
   path('institution/<str:uid>/edit/', institute_view.edit_institution_profile, name='edit_institution_profile'),
   path('institution/<str:uid>/manage-users/', institute_view.manage_institution_users, name='manage_institution_users'),
   # Coupon management URLs
   path('institution/<str:uid>/manage-coupons/', institute_view.manage_institution_coupons, name='manage_institution_coupons'),
   path('institution/<str:uid>/create-coupon/', institute_view.create_institution_coupon, name='create_institution_coupon'),
   path('institution/<str:uid>/edit-coupon/<int:coupon_id>/', institute_view.edit_institution_coupon, name='edit_institution_coupon'),
   path('institution/<str:uid>/delete-coupon/<int:coupon_id>/', institute_view.delete_institution_coupon, name='delete_institution_coupon'),
   # Reviews URL
   path('institution/<str:uid>/reviews/', institute_view.institution_reviews, name='institution_reviews'),
   path('institution/<str:uid>/submit-review/', institute_view.submit_institution_review, name='submit_institution_review'),
   path('institution/<str:uid>/edit-upi/', institute_view.edit_upi_details, name='edit_upi_details'),
   # Image management URLs
   path('institution/<str:uid>/update-image/', institute_view.update_institution_image, name='update_institution_image'),
   path('institution/<str:uid>/remove-image/', institute_view.remove_institution_image, name='remove_institution_image'),
   # Banner management URLs
   path('institution/<str:uid>/manage-banner/', institute_view.manage_institution_banner, name='manage_institution_banner'),
   path('institution/banner/<int:banner_id>/delete/', institute_view.delete_institution_banner, name='delete_institution_banner'),
]