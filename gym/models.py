import uuid
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

class GymCard(models.Model):
    card_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.card_id