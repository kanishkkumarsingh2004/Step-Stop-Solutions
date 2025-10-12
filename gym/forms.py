from django import forms
from .models import Gym, GymCard

class GymForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = ['venue_name']

class GymRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    mobile_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    opening_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))
    closing_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Gym
        fields = [
            'first_name', 'last_name', 'email', 'mobile_number', 'address',
            'venue_name', 'venue_location', 'description',
            'capacity', 'pincode', 'district', 'city', 'state',
            'social_media_links', 'equipment_available', 'additional_services',
            'opening_time', 'closing_time'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'venue_location': forms.Textarea(attrs={'rows': 3}),
            'equipment_available': forms.Textarea(attrs={'rows': 3}),
            'additional_services': forms.Textarea(attrs={'rows': 3}),
        }
        exclude = ['owner']

class GymCardForm(forms.ModelForm):
    class Meta:
        model = GymCard
        fields = ['card_id', 'user', 'gym', 'is_active']
