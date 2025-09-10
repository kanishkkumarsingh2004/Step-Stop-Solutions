from django.urls import path
from . import institute_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = "coaching"

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
   # Subscription management URLs
   path('institution/<str:uid>/manage-subscriptions/', institute_view.manage_institution_subscriptions, name='manage_institution_subscriptions'),
   path('institution/subscription/<int:subscription_id>/delete/', institute_view.delete_institution_subscription, name='delete_institution_subscription'),
   path('get-subscription/<int:subscription_id>/', institute_view.get_subscription, name='get_subscription'),
   path('update-subscription/<int:subscription_id>/', institute_view.update_subscription, name='update_subscription'),
   path('institute-details/<str:uid>/subscriptions/', institute_view.public_institute_subscriptions, name='public_institute_subscriptions'),
   path('subscription/<int:subscription_id>/apply-coupon/', institute_view.apply_subscription_coupon, name='apply_subscription_coupon'),
   path('institution/<str:uid>/subscription/<int:subscription_id>/payment/', institute_view.institute_subscription_payment, name='institute_subscription_payment'),
   path('institution/<str:uid>/subscription/<int:subscription_id>/process-payment/', institute_view.process_subscription_payment, name='process_subscription_payment'),
   path('institution/<str:uid>/subscription/<int:subscription_id>/details/', institute_view.institute_subscription_details, name='institute_subscription_details'),
   path('institution/<str:uid>/subscription/<int:subscription_id>/verify-payment/', institute_view.verify_payment, name='verify_payment'),
   path('institution/<str:uid>/payment-verifications/', institute_view.payment_verifications, name='payment_verifications'),
   path('institution/<str:uid>/payment-expenses/', institute_view.payment_expenses, name='payment_expenses'),
   path('institution/<str:uid>/add-expense/', institute_view.add_institution_expense, name='add_institution_expense'),
   path('institution/<str:uid>/expense-analytics/', institute_view.expense_analytics, name='expense_analytics'),
   path('institution/<str:institution_uid>/save_timetable/', institute_view.save_timetable, name='save_timetable'),
   path('institution/<str:institution_uid>/save-subject-faculty/', institute_view.save_subject_faculty, name='save_subject_faculty'),
   path('get-faculty-name/', institute_view.get_faculty_name_by_ssid, name='get_faculty_name_by_ssid'),
   path('institution/<str:institution_uid>/remove-subject/', institute_view.remove_subject, name='remove_subject'),
   path('institution/<str:uid>/schedule/', institute_view.view_schedule, name='view_schedule'),
   path('institution/<str:uid>/allocate-card/', institute_view.allocate_card_to_institution_page, name='allocate_card_to_institution_page'),
   path('institution/allocate-card-action/', institute_view.allocate_card_to_institution, name='allocate_card_to_institution_action'),
   # Staff Management
   path('institution/<str:uid>/manage-staff/', institute_view.manage_institution_staff, name='manage_institution_staff'),
   path('institution/<str:uid>/add-staff/', institute_view.add_institution_staff, name='add_institution_staff'),
   path('institution/staff/<int:staff_id>/update-permissions/', institute_view.update_institution_staff_permissions, name='update_institution_staff_permissions'),
   path('institution/staff/<int:staff_id>/remove/', institute_view.remove_institution_staff, name='remove_institution_staff'),
   path('institution/<str:uid>/staff-dashboard/', institute_view.institution_staff_dashboard, name='institution_staff_dashboard'),
   path('admin-dashboard/manage-cards/', institute_view.manage_institution_cards, name='manage_institution_cards'),
   path('institution/<str:uid>/attendance/', institute_view.coaching_attendance_page, name='institute_attendance_page'),
   path('mark-institute-attendance/', institute_view.mark_institute_attendance, name='mark_attendance'),

   # Installment Payments
   path('institution/<str:institution_uid>/installments/', institute_view.installment_payment_list, name='institution_installment_payment_list'),
   path('institution/<str:institution_uid>/subscription/<int:subscription_id>/installments/', institute_view.installment_payment_list, name='installment_payment_list'),
   path('institution/<str:institution_uid>/subscription/<int:subscription_id>/installments/add/', institute_view.add_installment_payment, name='add_installment_payment'),
   path('institution/<str:institution_uid>/subscription/<int:subscription_id>/installments/<int:installment_id>/edit/', institute_view.edit_installment_payment, name='edit_installment_payment'),
   path('institution/<str:institution_uid>/subscription/<int:subscription_id>/installments/<int:installment_id>/delete/', institute_view.delete_installment_payment, name='delete_installment_payment'),

   # Partial payment endpoints
   path('institution/<str:uid>/subscription/<int:subscription_id>/process-partial-payment/', institute_view.process_partial_payment, name='process_partial_payment'),
   path('institution/<str:uid>/subscription/<int:subscription_id>/make-additional-payment/', institute_view.make_additional_payment, name='make_additional_payment'),

   # Payment Reminders
   path('institution/<str:uid>/payment-reminders/', institute_view.payment_reminders, name='payment_reminders'),
   path('send-payment-reminder/', institute_view.send_payment_reminder, name='send_payment_reminder'),

   
]