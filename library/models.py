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
    nfc_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.TextField()
    mobile_number = models.CharField(max_length=15)
    emergency_number = models.CharField(max_length=15)
    dob = models.DateField()
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
    name = models.CharField(max_length=200)
    address = models.TextField()
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_institutions')
    description = models.TextField()
    institution_type = models.CharField(max_length=100, help_text="Type of institution")
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

    def __str__(self):
        return self.name

    @property
    def total_capacity(self):
        """Calculate total capacity from all classrooms"""
        return sum(classroom.get('capacity', 0) for classroom in self.classrooms.values())

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

class Attendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
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
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='admin_cards', null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_id} - {self.library.name}"
    
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