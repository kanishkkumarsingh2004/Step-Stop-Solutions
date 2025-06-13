from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
   # Authentication
   path('', views.home, name='home'),
   path('login/', views.user_login, name='login'),
   path('signup/', views.user_signup, name='signup'),
   path('logout/', views.user_logout, name='logout'),
   
   # Dashboards
   path('dashboard/', views.dashboard, name='dashboard'),
   path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
   path('library/<int:library_id>/dashboard/', views.library_dashboard, name='library_dashboard'),
   path('library/<int:library_id>/edit/', views.edit_library_profile, name='edit_library_profile'),
   
   # User Management
   path('vendor/<int:library_id>/manage-users/', views.manage_users, name='manage_users'),    
   # Library Management
   path('register-library/', views.register_library, name='register_library'),
   path('registered-lib/', views.register_venders_shop, name='register_lib'),
   path('registered-institute/', views.register_institute, name='register_institute'),
   path('manage-libraries/', views.manage_libraries, name='manage_libraries'),
   path('toggle-library-approval/<int:library_id>/', views.toggle_library_approval, name='toggle_library_approval'),
   path('manage-institutions/', views.manage_institutions, name='manage_institutions'),
   
   # Library Details
   path('library-details/<int:library_id>/', views.public_library_details, name='library_details'),
   path('admin-dashboard/library-details/<int:library_id>/', views.admin_library_details, name='admin_library_details'),
   
   # Subscriptions
   path('library/<int:library_id>/subscription/', views.subscription_page, name='subscription_page'),
   path('my-subscriptions/', views.user_subscriptions, name='user_subscriptions'),
   path('library/<int:library_id>/create-subscription/', views.create_subscription, name='create_subscription'),
   
   # Payments
   path('payment/<int:plan_id>/', views.payment_page, name='payment'),
   path('confirm-payment/<int:plan_id>/', views.confirm_payment, name='confirm_payment'),
   path('payment-confirmation/<str:transaction_id>/', views.payment_confirmation, name='payment_confirmation'),
   path('library/<int:library_id>/verify-payments/', views.verify_payments, name='verify_payments'),
   path('verify-payment/<int:transaction_id>/', views.verify_single_payment, name='verify_single_payment'),
   path('transactions/<int:transaction_id>/update-status/', views.update_transaction_status, name='update_transaction_status'),
   
   # Enrollment
   path('library/<int:library_id>/enroll/', views.enroll_library, name='enroll_library'),
   path('enrollment/success/', views.enrollment_success, name='enrollment_success'),
   
   # Attendance
   path('vendor/<int:vendor_id>/all-attendance/', views.all_attendance, name='all_attendance'),
   path('check-access/', views.check_access, name='check_access'),
   
   # Expenses
   path('library/<int:library_id>/expenses/', views.expense_dashboard, name='expense_dashboard'),
   path('library/<int:library_id>/add-expense/', views.add_expense, name='add_expense'),
   path('library/<int:library_id>/expenses/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
   path('library/<int:library_id>/expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
   
   # NFC
   path('library/<int:library_id>/nfc-add-user/', views.nfc_add_user_page, name='nfc_add_user_page'),
   path('allocate/', views.allocate, name='allocate'),
   path('deallocate-nfc/', views.deallocate_nfc, name='deallocate_nfc'),    
   # Attendance
   path('library/<int:library_id>/attendance/', views.attendance_page, name='attendance_page'),
   
   # Legal Pages
   path('terms-and-conditions/', views.terms_conditions, name='terms_conditions'),
   path('cookies-policy/', views.cookies_policy, name='cookies_policy'),
   path('disclaimer/', views.disclaimer, name='disclaimer'),
   path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
   path('library/<int:library_id>/staff-management/', views.staff_management, name='library_staff_management'),
   
   # Password Reset
   path('password-reset/', 
      auth_views.PasswordResetView.as_view(
         template_name='registration/password_reset_form.html',
         email_template_name='registration/password_reset_email.html',
         subject_template_name='registration/password_reset_subject.txt',
         success_url=reverse_lazy('password_reset_done')
      ), 
      name='password_reset'),
   path('password-reset/done/', 
      auth_views.PasswordResetDoneView.as_view(
         template_name='registration/password_reset_done.html'
      ), 
      name='password_reset_done'),
   path('password-reset-confirm/<uidb64>/<token>/', 
      auth_views.PasswordResetConfirmView.as_view(
         template_name='registration/password_reset_confirm.html',
         success_url=reverse_lazy('password_reset_complete')
      ), 
      name='password_reset_confirm'),
   path('password-reset-complete/', 
      auth_views.PasswordResetCompleteView.as_view(
         template_name='registration/password_reset_complete.html'
      ), 
      name='password_reset_complete'),
   
   # Staff Management
   path('library/<int:library_id>/add-staff/', views.add_staff, name='add_staff'),
   path('library/<int:library_id>/get-staff/', views.get_staff, name='get_staff'),
   path('search-user/', views.search_user, name='search_user'),
   
   # Admin Dashboard
   path('admin-dashboard/all-users/', views.all_users, name='all_users'),
   path('admin-dashboard/all-libraries/', views.all_libraries, name='all_libraries'),
   path('admin-dashboard/user-details/<int:user_id>/', views.user_details, name='user_details'),
   path('admin-dashboard/library-full-details/<int:library_id>/', views.admin_full_info_library_details, name='admin_full_info_library_details'),
   
   # Vendor Type Selection
   path('vendor-type/', views.vender_type, name='vender_type'),
   

   
   # Subscriptions
   path('library/<int:library_id>/manage-subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
   path('check_nfc_allocation/', views.check_nfc_allocation, name='check_nfc_allocation'),

   # Expense Chart
   path('library/<int:library_id>/expense-chart/', views.expense_chart, name='expense_chart'),

   # Profile
   path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
   path('profile/update/<int:user_id>/', views.update_profile, name='update_profile'),

   # Password Change
   path('password-change/', auth_views.PasswordChangeView.as_view(template_name='authentication/password_change.html'), name='password_change'),
   path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='authentication/password_change_done.html'), name='password_change_done'),
   path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
   path('edit-subscription/', views.edit_subscription, name='edit_subscription'),
   path('library/<int:library_id>/create-coupon/', views.create_coupon, name='create_coupon'),
   path('<int:library_id>/manage-coupons/', views.manage_coupons, name='manage_coupons'),
   path('coupons/<int:coupon_id>/toggle-status/', views.toggle_coupon_status, name='toggle_coupon_status'),
   path('handle-payment-success/', views.handle_payment_success, name='handle_payment_success'),
   path('coupons/<int:coupon_id>/edit/', views.edit_coupon, name='edit_coupon'),
   path('coupons/<int:coupon_id>/delete/', views.delete_coupon, name='delete_coupon'),

   # Add this URL pattern if it doesn't exist
   path('payment-confirmation/<str:transaction_id>/', views.payment_confirmation, name='payment_confirmation'),
   path('appoint-staff/<int:library_id>/<int:user_id>/', views.appoint_staff, name='appoint_staff'),
   path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
   path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
   path('library/<int:library_id>/update-upi-data/', views.update_upi_data, name='update_upi_data'),
   path('remove-staff/<int:library_id>/<int:user_id>/', views.remove_staff, name='remove_staff'),
   path('library/<int:library_id>/staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
   path('library/<int:library_id>/manage-banner/', views.manage_banner, name='manage_banner'),
   path('banner/<int:banner_id>/delete/', views.delete_banner, name='delete_banner'),
   path('<int:library_id>/update_image/', views.update_library_image, name='update_library_image'),
   path('<int:library_id>/remove_image/', views.remove_library_image, name='remove_library_image'),
   path('update-banner/', views.update_banner, name='update_banner'),
   path('manage-home-banners/', views.manage_home_banners, name='manage_home_banners'),
   path('delete-home-banner/<int:banner_id>/', views.delete_home_banner, name='delete_home_banner'),
   path('manage-text-banner/', views.manage_text_banner, name='manage_text_banner'),
   path('delete-text-banner/<int:banner_id>/', views.delete_text_banner, name='delete_text_banner'),
   path('manage-banner-counts/', views.manage_banner_counts, name='manage_banner_counts'),
   path('library/<int:library_id>/add-review/', views.add_review, name='add_review'),
   path('library/<int:library_id>/manage-reviews/', views.manage_reviews, name='manage_reviews'),
   path('library/<int:library_id>/reviews/', views.view_reviews, name='view_reviews'),
   path('apply-vendor/', views.apply_vendor, name='apply_vendor'),
   # Registration Views
   path('apply-vendor/apply-for-vendor/library/', views.register_library, name='register_library'),
   path('apply-vendor/apply-for-vendor/', views.apply_for_vendor, name='apply_for_vendor'),
   path('about-us/', views.about_us, name='about_us'),
   path('add-permission/<int:library_id>/<int:staff_id>/', views.add_permission, name='add_permission'),
   path('remove-permission/<int:library_id>/<int:staff_id>/', views.remove_permission, name='remove_permission'),
   path('manage-permissions/<int:library_id>/<int:staff_id>/', views.manage_permissions, name='manage_permissions'),
   path('get-permissions/<int:library_id>/<int:staff_id>/', views.get_permissions, name='get_permissions'),
   path('vendor/<int:library_id>/user/<int:user_id>/', views.library_user_details, name='library_user_details'),
   path('mark-attendance/<int:user_id>/', views.mark_attendance_manual, name='mark_attendance_manual'),
   path('manage-cards/', views.manage_cards, name='manage_cards'),
   path('add-card/', views.add_card, name='add_card'),
   path('check_card_in_admin_db/', views.check_card_in_admin_db, name='check_card_in_admin_db'),
   path('delete-card/<int:card_id>/', views.delete_card, name='delete_card'),
   path('allocate-card-to-vendor-page/', views.allocate_card_to_library_page, name='allocate_card_to_vendor_page'),
   path('allocate-card-to-library/', views.allocate_card_to_library, name='allocate_card_to_library'),
   path('deallocate-card/<int:card_id>/', views.deallocate_card, name='deallocate_card'),
   path('allocate-card-count/', views.allocate_card_count, name='allocate_card_count'),

   # Admin Graphs
   path('admin-graphs/', views.admin_graphs, name='admin_graphs'),
   path('manage-admin-loss/', views.Manage_Admin_loss, name='Manage_Admin_Loss'),
   path('edit-admin-loss/<int:expense_id>/', views.EditAdminExpense_loss, name='edit_admin_expense'),
   path('delete-admin-loss/<int:expense_id>/', views.DeleteAdminExpense_loss, name='delete_admin_expense'),

   path('manage-admin-profit/', views.Manage_Admin_profit, name='Manage_Admin_Profit'),

   path('balance-sheet/', views.balance_sheet, name='balance_sheet'),

]