from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from shortuuid.django_fields import ShortUUIDField 
from django.core.exceptions import ValidationError
import re
from django.db.models import Avg
import logging

logger = logging.getLogger(__name__)

class Library(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='libraries'
    )
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='owned_libraries')
    description = models.TextField()
    venue_location = models.TextField(help_text="Detailed location of the venue")
    venue_name = models.CharField(max_length=200, help_text="Name of the venue")
    business_type = models.CharField(max_length=50)
    max_banners = models.PositiveIntegerField(default=2, help_text="Maximum number of banners allowed")
    social_media_links = models.TextField(blank=True, null=True, help_text="Comma separated list of social media links")
    capacity = models.PositiveIntegerField(help_text="Maximum capacity of the venue")
    equipment_available = models.TextField(blank=True, null=True, help_text="List of available equipment")
    additional_services = models.TextField(blank=True, null=True, help_text="Any additional services offered")
    is_approved = models.BooleanField(default=False, help_text="Approval status of the application")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField('CustomUser', related_name='joined_libraries', blank=True)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    pincode = models.CharField(max_length=10, help_text="Pincode of the venue location")
    district = models.CharField(max_length=100, help_text="District of the venue location")
    city = models.CharField(max_length=100, help_text="City of the venue location")
    state = models.CharField(max_length=100, help_text="State of the venue location")
    staff = models.ManyToManyField('CustomUser', related_name='libraries_staffed', blank=True)
    upi_id = models.CharField(max_length=50)
    recipient_name = models.CharField(max_length=100)
    thank_you_message = models.CharField(max_length=200)
    available_seats = models.PositiveIntegerField(default=0)
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_reviews(self):
        return self.reviews.all().order_by('-created_at')

    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    def save(self, *args, **kwargs):
        if not self.pk and self.available_seats == 0:
            self.available_seats = self.capacity
        super().save(*args, **kwargs)

    @property
    def business_hours(self):
        if self.opening_time == self.closing_time:
            return "24 hours"
        else:
            opening_hour = self.opening_time.hour
            closing_hour = self.closing_time.hour
            duration = closing_hour - opening_hour
            if duration < 0:
                duration += 24
            return f"{duration} hours"

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('GEN', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('PWD', 'PWD'),
        ('OTHER', 'Others'),
    ]

    EDUCATION_CHOICES = [
        ('Matriculation', 'Matriculation'),
        ('Intermediate', 'Intermediate'),
        ('Diploma', 'Diploma'),
        ('Bachelor\'s Degree', 'Bachelor\'s Degree'),
        ('Master\'s Degree', 'Master\'s Degree'),
        ('PhD', 'PhD'),
        ('Other', 'Other'),
    ]

    library = models.ManyToManyField(Library, related_name='library_users', blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.TextField()
    mobile_number = models.CharField(max_length=15)
    emergency_number = models.CharField(max_length=15)
    dob = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    pincode = models.CharField(max_length=6)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    is_checked_in = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    vendor_ssids = models.ManyToManyField('VendorSSID', blank=True)
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='GEN',
        help_text="Select your category"
    )
    ssid = ShortUUIDField(length=5, max_length=5, unique=True, blank=True, null=True, alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz')
    accepted_terms = models.BooleanField(default=False)
    accepted_privacy_policy = models.BooleanField(default=False)
    profile_image_url = models.URLField(max_length=1000, blank=True, null=True)
    profile_image_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.profile_image_url:
            self.profile_image_id = self.extract_drive_file_id(self.profile_image_url)
        super().save(*args, **kwargs)

    @staticmethod
    def extract_drive_file_id(url):
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_permissions_for_library(self, library):
        try:
            vendor_ssid = self.vendor_ssids.filter(library=library).first()
            if vendor_ssid and vendor_ssid.permissions:
                return vendor_ssid.permissions.split(',')
            return []
        except Exception as e:
            logger.error(f"Error getting permissions for library: {str(e)}")
            return []

    class Meta:
        permissions = [
            ("view_user_details", "Can view user details"),
        ]

class Institution(models.Model):
    uid = ShortUUIDField(length=20, max_length=20, unique=True, alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz')
    name = models.CharField(max_length=200)
    address = models.TextField()
    pincode = models.CharField(max_length=6, help_text="6-digit postal code")
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_institutions')
    description = models.TextField()
    website_url = models.URLField(blank=True, null=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    business_type = models.CharField(max_length=50)
    classrooms = models.JSONField(default=dict, help_text="JSON containing classroom information with capacities")
    facilities_available = models.TextField(blank=True, null=True, help_text="List of available facilities")
    additional_services = models.TextField(blank=True, null=True, help_text="Any additional services offered")
    is_approved = models.BooleanField(default=False, help_text="Approval status of the application")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    upi_id = models.CharField(max_length=255, blank=True, null=True, help_text="UPI ID for receiving payments")
    recipient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the UPI payment recipient")
    thank_you_message = models.TextField(blank=True, null=True, help_text="Message to show after successful payment")
    max_banners = models.PositiveIntegerField(default=2, help_text="Maximum number of banners allowed")

    def __str__(self):
        return self.name

    @property
    def total_capacity(self):
        """Calculate total capacity from all classrooms"""
        return sum(classroom.get('capacity', 0) for classroom in self.classrooms.values())

    def get_reviews(self):
        return self.reviews.all().order_by('-created_at')

    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

class SubscriptionPlan(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, help_text="The vendor who created this subscription plan")
    name = models.CharField(max_length=255, help_text="Name of the subscription plan")
    start_date = models.DateField(help_text="The date when the subscription plan was created")
    duration_in_months = models.IntegerField(help_text="Duration of the subscription plan in months")
    duration_in_hours = models.IntegerField(default=0, help_text="Duration of the subscription plan in hours (if applicable)")
    normal_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="The normal price of the subscription plan")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="The discounted price of the subscription plan (if any)")
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='subscription_plans', null=True)

    def __str__(self):
        return f"{self.name} - {self.normal_price}₹"

    @property
    def has_discount(self):
        return self.discount_price is not None

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.status == 'valid'

    def __str__(self):
        return f"Transaction {self.transaction_id} by {self.user.email}"

class LibraryAttendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='library_attendances')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_color = models.IntegerField(default=0)
    check_out_color = models.IntegerField(default=0)
    duration_color = models.IntegerField(default=0)
    nfc_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'library', 'check_in_time')

    def __str__(self):
        return f"{self.user.email} - {self.library.venue_name} - {self.check_in_time}"


class CoachingAttendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='coaching_attendances')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_in_color = models.IntegerField(default=0)
    check_out_color = models.IntegerField(default=0)
    duration_color = models.IntegerField(default=0)
    nfc_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'institution', 'check_in_time')

    def __str__(self):
        return f"{self.user.email} - {self.institution.name} - {self.check_in_time}"

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="valid")

    def __str__(self):
        return f"{self.user.email} - {self.subscription.name}"

    def save(self, *args, **kwargs):
        # Update status based on end date
        today = timezone.now().date()
        if self.end_date < today:
            self.status = 'expired'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def save(self, *args, **kwargs):
        # Update status based on end date
        today = timezone.now().date()
        if self.end_date < today:
            self.status = 'expired'
        super().save(*args, **kwargs)

class Expense(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
    ]

    expense_name = models.CharField(max_length=255)
    expense_description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='CASH')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='expenses')

    def __str__(self):
        return f"{self.expense_name} - ₹{self.amount} ({self.date})"

    def clean(self):
        if self.payment_mode in ['CARD', 'UPI'] and not self.transaction_id:
            raise ValidationError("Transaction ID is required for Card/UPI payments")

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_usage = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_coupons')
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    library = models.ForeignKey('Library', on_delete=models.CASCADE, related_name='coupons', null=True)

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.times_used < self.max_usage and
            self.valid_from <= now <= self.valid_to
        )
    def increment_usage(self):
        self.times_used = models.F('times_used') + 1
        self.save(update_fields=['times_used'])

    def apply_discount(self, price):
        if self.discount_type == 'percentage':
            return price * (1 - self.discount_value / 100)
        return max(price - self.discount_value, 0)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'}) - {self.library.venue_name if self.library else 'Global'}"
    
class Banner(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='banners')
    google_drive_link = models.CharField(max_length=1000)
    google_drive_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.google_drive_link:
            self.google_drive_id = self.extract_file_id(self.google_drive_link)
        super().save(*args, **kwargs)

    @staticmethod
    def extract_file_id(url):
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def __str__(self):
        return f"Banner for {self.library.venue_name}"

class LibraryImage(models.Model):
    library = models.OneToOneField(Library, on_delete=models.CASCADE, related_name='image')
    google_drive_link = models.URLField(max_length=500)
    google_drive_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.google_drive_link:
            self.google_drive_id = self.extract_file_id(self.google_drive_link)
        super().save(*args, **kwargs)

    @staticmethod
    def extract_file_id(url):
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def __str__(self):
        return f"Image for {self.library.venue_name}"
    
class HomePageTextBanner(models.Model):
    text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text
    
class HomePageImageBanner(models.Model):
    google_drive_link = models.CharField(max_length=1000)
    google_drive_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.google_drive_link:
            self.google_drive_id = Banner.extract_file_id(self.google_drive_link)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Home Page Banner ({'Active' if self.is_active else 'Inactive'})"

class Review(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rating} stars"

class VendorSSID(models.Model):
    PERMISSION_CHOICES = [
        ('manage_users', 'Manage Users'),
        ('nfc_add_user', 'Add User via NFC'),
        ('attendance', 'Attendance'),
        ('view_vendor_details', 'View Vendor Details'),
        ('view_expenses', 'View Expense Page'),
        ('view_all_attendance', 'View All Attendance'),
        ('verify_payments', 'Verify Payments')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    permissions = models.CharField(max_length=255, choices=PERMISSION_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.library}"

class AdminCard(models.Model):
    card_id = models.CharField(max_length=100, unique=True)
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='admin_cards', null=True, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='admin_cards', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.library:
            return f"{self.card_id} - {self.library.venue_name}"
        elif self.institution:
            return f"{self.card_id} - {self.institution.name}"
        return f"{self.card_id} - Unallocated"

    def is_allocated(self):
        """Check if the card is allocated to any entity."""
        return self.library is not None or self.institution is not None

    def clean(self):
        allocations = [self.library, self.institution]
        num_allocations = sum(1 for item in allocations if item is not None)

        if num_allocations > 1:
            raise ValidationError("A card can only be allocated to one entity (library, institution) at a time.")
        if num_allocations == 0:
            raise ValidationError("A card must be allocated to either a library, an institution")
    
class AdminExpense(models.Model):
    TYPE_CHOICES = [
        ('Profit', 'Profit'),
        ('Loss', 'Loss'),
    ]
    
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='Loss')
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ₹{self.amount} ({self.get_type_display()}) - {self.date}"

class InstitutionCoupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('EXPIRED', 'Expired'),
    ]

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_usage = models.PositiveIntegerField(default=1)
    current_usage = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    applicable_plans = models.ManyToManyField('InstitutionSubscriptionPlan', blank=True, help_text="Subscription plans this coupon can be applied to")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.institution.name}"

    def is_valid(self):
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.valid_from <= now <= self.valid_to and
            self.current_usage < self.max_usage
        )

    def is_applicable_to_plan(self, subscription_plan):
        """
        Check if this coupon is applicable to a specific subscription plan.
        If no plans are specified in applicable_plans, the coupon applies to all plans.
        """
        if not self.applicable_plans.exists():
            return True
        return subscription_plan in self.applicable_plans.all()

    def has_been_used_by_user(self, user):
        """
        Check if this coupon has already been used by the given user.
        """
        return self.used_by.filter(user=user).exists()

    def apply_discount(self, amount):
        if not self.is_valid():
            return amount
        
        if self.discount_type == 'PERCENTAGE':
            discount = (amount * self.discount_value) / 100
        else:  # FIXED
            discount = self.discount_value
        
        return max(0, amount - discount)

    def use_coupon(self, user):
        """
        Mark the coupon as used by a specific user.
        Returns True if successful, False if the coupon cannot be used.
        """
        if not self.is_valid() or self.has_been_used_by_user(user):
            return False
            
        self.current_usage += 1
        if self.current_usage >= self.max_usage:
            self.status = 'INACTIVE'
        self.save()
        
class InstitutionReview(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['institution', 'user']  # Ensure one review per user per institution

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rating} stars"

class InstitutionImage(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='images')
    google_drive_link = models.URLField(max_length=500)
    google_drive_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Image for {self.institution.name}"

    def save(self, *args, **kwargs):
        # Extract Google Drive ID from link if provided
        if self.google_drive_link:
            self.google_drive_id = self.extract_file_id(self.google_drive_link)
        super().save(*args, **kwargs)

    @staticmethod
    def extract_file_id(url):
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

class InstitutionBanner(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='banners')
    google_drive_link = models.CharField(max_length=1000)
    google_drive_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.google_drive_link:
            self.google_drive_id = self.extract_file_id(self.google_drive_link)
        super().save(*args, **kwargs)

    @staticmethod
    def extract_file_id(url):
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def __str__(self):
        return f"Banner for {self.institution.name}"
    
class InstitutionSubscriptionPlan(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='subscription_plans')
    name = models.CharField(max_length=255, help_text="Name of the subscription plan")
    course_description = models.TextField(help_text="Description of the course", blank=True, null=True)
    faculty_description = models.TextField(help_text="Description of the faculty members", blank=True, null=True)
    subject_cover = models.TextField(help_text="List of subjects covered in this course", blank=True, null=True)
    exam_cover = models.TextField(help_text="List of exams covered in this course", blank=True, null=True)
    start_time = models.TimeField(help_text="Start time of the course")
    end_time = models.TimeField(help_text="End time of the course")
    start_date = models.DateField(help_text="Start date of the subscription")
    course_duration = models.PositiveIntegerField(help_text="Duration of the course in months")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original price of the subscription")
    new_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discounted price of the subscription")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.institution.name}"

    @property
    def has_discount(self):
        return self.new_price < self.old_price

    class Meta:
        verbose_name = "Institution Subscription Plan"
        verbose_name_plural = "Institution Subscription Plans"
        ordering = ['-created_at']

class InstitutionSubscription(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='institution_subscriptions')
    subscription_plan = models.ForeignKey(InstitutionSubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='valid')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    coupon_applied = models.ForeignKey(InstitutionCoupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.subscription_plan.name}"

    def save(self, *args, **kwargs):
        # Update status based on end date
        today = timezone.now().date()
        if self.end_date < today:
            self.status = 'expired'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Institution Subscription"
        verbose_name_plural = "Institution Subscriptions"
        ordering = ['-created_at']

class PaymentVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    subscription = models.ForeignKey(InstitutionSubscription, on_delete=models.CASCADE, related_name='verifications')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='verified_payments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    verification_notes = models.TextField(blank=True, null=True)
    screenshot_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Verification"
        verbose_name_plural = "Payment Verifications"

    def __str__(self):
        return f"Payment Verification for {self.subscription} - {self.status}"

class InstitutionExpense(models.Model):
    EXPENSE_TYPES = [
        ('water', 'Water Bill'),
        ('wifi', 'WiFi Bill'),
        ('rent', 'Rent'),
        ('electricity', 'Electricity Bill'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Institution Expense'
        verbose_name_plural = 'Institution Expenses'

    def __str__(self):
        return f"{self.institution.name} - {self.get_expense_type_display()}: {self.description} - ₹{self.amount}"
    
class TimetableEntry(models.Model):
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE)
    day = models.CharField(max_length=10)  # e.g., 'Monday'
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=100)
    faculty_ssid = models.CharField(max_length=20)
    faculty_name = models.CharField(max_length=100, blank=True, null=True)
    classroom = models.CharField(max_length=100, blank=True, null=True)
    cell_row = models.IntegerField(default=0)  # New: row index in timetable
    cell_col = models.IntegerField(default=0)  # New: column index in timetable

    def __str__(self):
        return f"{self.institution} - {self.day} - {self.classroom} - {self.subject} (row {self.cell_row}, col {self.cell_col})"

# New model for subject-faculty mapping
class SubjectFacultyMap(models.Model):
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE, related_name='subject_faculty_maps')
    subject = models.CharField(max_length=100)
    faculty_ssid = models.CharField(max_length=10)
    faculty_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('institution', 'subject')

    def __str__(self):
        return f"{self.institution.name} - {self.subject} -> {self.faculty_ssid}"

class InstitutionCardLog(models.Model):
    """A log of card allocations for institutions."""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='card_allocation_logs')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='institution_card_logs')
    card_id = models.CharField(max_length=100)
    allocated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='institution_allocations_logged')
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('institution', 'user', 'card_id')
        ordering = ['-timestamp']

    def __str__(self):
        return f"Card {self.card_id} <-> {self.user.get_full_name()} @ {self.institution.name}"

class LibraryCardLog(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='card_allocation_logs')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='library_card_logs')
    card_id = models.CharField(max_length=100)
    allocated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='library_allocations_logged')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('library', 'user', 'card_id')
        ordering = ['-timestamp']

    def __str__(self):
        return f"Card {self.card_id} <-> {self.user.get_full_name()} @ {self.library.venue_name}"

class UserRoleNumber(models.Model):
    """Model to store role numbers for users in specific libraries."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='role_numbers')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='user_role_numbers')
    role_number = models.CharField(max_length=50, help_text="Role number for this user in this library")
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='assigned_role_numbers')
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'library', 'role_number')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - Role {self.role_number} @ {self.library.venue_name}"


class InstitutionStaff(models.Model):
    PERMISSION_CHOICES = [
        ('manage_profile', 'Manage Institution Profile'),
        ('manage_staff', 'Manage Staff'),
        ('manage_users', 'Manage Enrolled Users'),
        ('manage_coupons', 'Manage Coupons'),
        ('manage_subscriptions', 'Manage Subscription Plans'),
        ('manage_payments', 'Verify Payments & View Expenses'),
        ('manage_schedule', 'Manage Timetable/Schedule'),
        ('manage_cards', 'Manage NFC Cards'),
        ('view_dashboard', 'View Dashboard Analytics'),
    ]

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='staff')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='staff_in_institutions')
    permissions = models.CharField(max_length=500, blank=True, help_text="Comma-separated list of permission keys.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Staff {self.user.get_full_name()} at {self.institution.name}"

    def get_permissions(self):
        return self.permissions.split(',') if self.permissions else []

    def has_perm(self, perm):
        return perm in self.get_permissions()

class InstallmentPayment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
    ]
    
    subscription = models.ForeignKey('InstitutionSubscription', on_delete=models.CASCADE, related_name='installments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Installment for {self.subscription} - Amount: ₹{self.amount_paid} - Status: {self.status}"

    class Meta:
        verbose_name = "Installment Payment"
        verbose_name_plural = "Installment Payments"
        ordering = ['-payment_date']

class PartialPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
    ]

    subscription = models.ForeignKey('InstitutionSubscription', on_delete=models.CASCADE, related_name='partial_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Partial payment amount")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes for the payment")
    verified = models.BooleanField(default=False, help_text="Whether this partial payment has been verified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Partial Payment for {self.subscription} - ₹{self.amount} ({self.payment_method})"

    class Meta:
        verbose_name = "Partial Payment"
        verbose_name_plural = "Partial Payments"
        ordering = ['-payment_date']
