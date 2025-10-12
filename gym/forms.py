from django import forms
from .models import Gym, GymCard, GymSubscriptionPlan, GymUserSubscription, GymTransaction, GymExpense

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

class GymUPIForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = ['upi_id', 'recipient_name', 'thank_you_message']
        widgets = {
            'upi_id': forms.TextInput(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out'}),
            'recipient_name': forms.TextInput(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out'}),
            'thank_you_message': forms.Textarea(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out', 'rows': 3}),
        }

class GymSubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = GymSubscriptionPlan
        fields = ['name', 'duration_in_months', 'duration_in_hours', 'normal_price', 'discount_price']

class GymUserSubscriptionForm(forms.ModelForm):
    class Meta:
        model = GymUserSubscription
        fields = ['user', 'subscription', 'start_date', 'end_date', 'start_time', 'end_time']

class GymTransactionForm(forms.ModelForm):
    class Meta:
        model = GymTransaction
        fields = ['user', 'subscription', 'transaction_id', 'amount', 'status']

class GymExpenseForm(forms.ModelForm):
    class Meta:
        model = GymExpense
        fields = ['expense_name', 'expense_description', 'amount', 'date', 'payment_mode', 'transaction_id']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'expense_description': forms.Textarea(attrs={'rows': 3}),
        }
