import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone

def generate_gym_id():
    return str(uuid.uuid4())[:30]

class Gym(models.Model):
    id = models.CharField(max_length=30, primary_key=True, default=generate_gym_id, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gyms_user')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_gyms')
    description = models.TextField()
    venue_location = models.TextField(help_text="Detailed location of the venue")
    venue_name = models.CharField(max_length=200, help_text="Name of the venue")
    business_type = models.CharField(max_length=50, default='Gym')
    max_banners = models.PositiveIntegerField(default=2, help_text="Maximum number of banners allowed")
    social_media_links = models.TextField(blank=True, null=True, help_text="Comma separated list of social media links")
    capacity = models.PositiveIntegerField(help_text="Maximum capacity of the venue")
    equipment_available = models.TextField(blank=True, null=True, help_text="List of available equipment")
    additional_services = models.TextField(blank=True, null=True, help_text="Any additional services offered")
    is_approved = models.BooleanField(default=False, help_text="Approval status of the application")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_gyms', blank=True)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    pincode = models.CharField(max_length=10, help_text="Pincode of the venue location")
    district = models.CharField(max_length=100, help_text="District of the venue location")
    city = models.CharField(max_length=100, help_text="City of the venue location")
    state = models.CharField(max_length=100, help_text="State of the venue location")
    staff = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='gyms_staffed', blank=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    thank_you_message = models.CharField(max_length=200, blank=True, null=True)
    available_seats = models.PositiveIntegerField(default=0)
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_seats = self.capacity
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

class GymCard(models.Model):
    card_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.card_id

class GymAttendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.gym.venue_name} - {self.date}"

    @property
    def duration(self):
        if self.check_in_time and self.check_out_time:
            return self.check_out_time - self.check_in_time
        return None

class GymSubscriptionPlan(models.Model):
    user = models.ForeignKey('library.CustomUser', on_delete=models.CASCADE, help_text="The vendor who created this subscription plan")
    name = models.CharField(max_length=255, help_text="Name of the subscription plan")
    duration_in_months = models.IntegerField(help_text="Duration of the subscription plan in months")
    duration_in_hours = models.IntegerField(default=0, help_text="Duration of the subscription plan in hours (if applicable)")
    normal_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="The normal price of the subscription plan")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="The discounted price of the subscription plan (if any)")
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='subscription_plans', null=True)

    def __str__(self):
        return f"{self.name} - {self.normal_price}₹"

    @property
    def has_discount(self):
        return self.discount_price is not None

    class Meta:
        verbose_name = "Gym Subscription Plan"
        verbose_name_plural = "Gym Subscription Plans"

class GymUserSubscription(models.Model):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey('library.CustomUser', on_delete=models.CASCADE)
    subscription = models.ForeignKey(GymSubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="valid")

    def __str__(self):
        return f"{self.user.email} - {self.subscription.name}"

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        if self.end_date < today:
            self.status = 'expired'
        super().save(*args, **kwargs)

    @property
    def days_left(self):
        today = timezone.now().date()
        if self.end_date >= today:
            return (self.end_date - today).days
        return 0

    class Meta:
        verbose_name = "Gym User Subscription"
        verbose_name_plural = "Gym User Subscriptions"

class GymTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
    ]

    user = models.ForeignKey('library.CustomUser', on_delete=models.CASCADE, related_name='gym_transactions')
    subscription = models.ForeignKey(GymSubscriptionPlan, on_delete=models.CASCADE, related_name='gym_transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.status == 'valid'

    def __str__(self):
        return f"Gym Transaction {self.transaction_id} by {self.user.email}"

class GymExpense(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
    ]

    expense_name = models.CharField(max_length=255)
    expense_description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='CASH')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='expenses')

    def __str__(self):
        return f"{self.expense_name} - ₹{self.amount} ({self.date})"

    def clean(self):
        if self.payment_mode in ['UPI'] and not self.transaction_id:
            raise ValidationError("Transaction ID is required for UPI payments")

class GymReview(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('library.CustomUser', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.get_full_name()} for {self.gym.venue_name}"

    class Meta:
        unique_together = ('gym', 'user')  # One review per user per gym

class GymCoupon(models.Model):
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
    created_by = models.ForeignKey('library.CustomUser', on_delete=models.CASCADE, related_name='created_gym_coupons')
    applicable_plans = models.ManyToManyField('GymSubscriptionPlan', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='coupons', null=True)
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
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'}) - {self.gym.venue_name if self.gym else 'Global'}"
