from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, 
    SubscriptionPlan, 
    Transaction, 
    LibraryAttendance, 
    Library, 
    UserSubscription
)


# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'category', 'joined_libraries')
    list_filter = ('is_staff', 'is_active', 'category')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'mobile_number', 'address', 'category')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Library/Coaching', {'fields': ('library',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'mobile_number', 'address', 'category', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('library',)

    def joined_libraries(self, obj):
        return ", ".join([lib.venue_name for lib in obj.library.all()])
    joined_libraries.short_description = 'Joined Libraries/Coaching'

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'start_date', 'duration_in_hours', 'duration_in_months', 'normal_price', 'library')
    search_fields = ('user__email', 'name')
    list_filter = ('start_date', 'library')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'subscription', 'status', 'amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('transaction_id',)

    def amount(self, obj):
        return obj.subscription.cost
    amount.short_description = 'Amount'

@admin.register(LibraryAttendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'library', 'check_in_time', 'check_out_time')
    search_fields = ('user__email', 'user__nfc_id', 'library__venue_name')
    list_filter = ('library', 'check_in_time', 'check_out_time')
    readonly_fields = ('check_in_time', 'check_out_time')

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 
        'last_name', 
        'venue_name', 
        'business_type', 
        'is_approved', 
        'created_at',
        'city',
        'state',
        'pincode'
    )
    list_filter = ('is_approved', 'business_type', 'created_at', 'city', 'state')
    search_fields = ('first_name', 'last_name', 'venue_name', 'city', 'state', 'pincode')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'first_name', 
                'last_name', 
                'address', 
                'description', 
                'venue_location', 
                'venue_name'
            )
        }),
        ('Business Details', {
            'fields': (
                'business_type', 
                'social_media_links', 
                'business_hours', 
                'capacity'
            )
        }),
        ('Additional Information', {
            'fields': (
                'equipment_available', 
                'additional_services'
            )
        }),
        ('Status', {
            'fields': (
                'is_approved', 
                'created_at', 
                'updated_at'
            )
        }),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'start_date', 'end_date')
    search_fields = ('user__email', 'subscription__name')
    list_filter = ('start_date', 'end_date')
    raw_id_fields = ('user', 'subscription')

