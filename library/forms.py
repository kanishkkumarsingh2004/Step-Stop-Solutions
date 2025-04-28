from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Library, SubscriptionPlan, CustomUser, Expense, Coupon, Banner, LibraryImage, HomePageImageBanner, Review
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    mobile_number = forms.CharField(max_length=15, required=True)
    emergency_number = forms.CharField(max_length=15, required=True)
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    email = forms.EmailField(required=True)
    category = forms.ChoiceField(choices=CustomUser.CATEGORY_CHOICES, required=True)
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    pincode = forms.CharField(max_length=6, required=True)
    district = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    age = forms.IntegerField(required=False)
    education = forms.ChoiceField(choices=CustomUser.EDUCATION_CHOICES, required=True)
    terms = forms.BooleanField(required=True)
    privacy = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'mobile_number', 'emergency_number', 'gender', 'address', 'password1', 'password2', 'category', 'dob', 'pincode', 'district', 'city', 'state', 'age', 'education', 'terms', 'privacy']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.accepted_terms = self.cleaned_data['terms']
        user.accepted_privacy_policy = self.cleaned_data['privacy']
        if commit:
            user.save()
        return user

class LibraryRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    mobile_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)

    class Meta:
        model = Library
        fields = [
            'first_name', 'last_name', 'email', 'mobile_number', 'address',
            'venue_name', 'venue_location', 'description', 
            'business_hours', 'capacity', 'pincode', 
            'district', 'city', 'state', 'social_media_links', 
            'equipment_available', 'additional_services'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'venue_location': forms.Textarea(attrs={'rows': 3}),
            'social_media_links': forms.Textarea(attrs={'rows': 2}),
            'equipment_available': forms.Textarea(attrs={'rows': 3}),
            'additional_services': forms.Textarea(attrs={'rows': 3}),
        }

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'duration_in_months', 'duration_in_hours', 'normal_price', 'discount_price']

class ExpenseForm(forms.ModelForm):
    EXPENSE_NAME_CHOICES = [
        ('Wifi', 'Wifi'),
        ('Water', 'Water'),
        ('Chair', 'Chair'),
        ('Table', 'Table'),
        ('Light', 'Light'),
        ('Books', 'Books'),
        ('Electricity Bills', 'Electricity Bills'),
        ('Rent Paid', 'Rent Paid'),
        ('Stationary Items', 'Stationary Items'),
        ('Legal Charges', 'Legal Charges'),
        ('Others', 'Others'),
    ]

    expense_name = forms.ChoiceField(choices=EXPENSE_NAME_CHOICES)
    expense_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    payment_mode = forms.ChoiceField(choices=Expense.PAYMENT_MODE_CHOICES)
    transaction_id = forms.CharField(required=False, max_length=100)

    class Meta:
        model = Expense
        fields = ['expense_name', 'expense_description', 'amount', 'date', 'payment_mode', 'transaction_id']

    def clean(self):
        cleaned_data = super().clean()
        payment_mode = cleaned_data.get('payment_mode')
        transaction_id = cleaned_data.get('transaction_id')

        if payment_mode in ['CARD', 'UPI'] and not transaction_id:
            raise forms.ValidationError("Transaction ID is required for Card/UPI payments")
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['mobile_number', 'emergency_number', 'category', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 
                 'max_usage', 'is_active', 'applicable_plans']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'applicable_plans': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        library_id = kwargs.pop('library_id', None)
        super().__init__(*args, **kwargs)
        if library_id:
            self.fields['applicable_plans'].queryset = SubscriptionPlan.objects.filter(library_id=library_id)
            if not self.instance.pk or self.instance.code != self.initial.get('code'):
                self.fields['code'].validators.append(self.validate_unique_code(library_id))

    def validate_unique_code(self, library_id):
        def validator(value):
            if Coupon.objects.filter(code=value, library_id=library_id).exists():
                raise ValidationError('This coupon code already exists for this library.')
        return validator
    
class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['google_drive_link']
        widgets = {
            'google_drive_link': forms.URLInput(attrs={
                'pattern': 'https://drive\.google\.com/.*',
                'placeholder': 'Enter Google Drive link',
                'required': True
            })
        }

    def clean_google_drive_link(self):
        link = self.cleaned_data.get('google_drive_link')
        if not link.startswith('https://drive.google.com/'):
            raise forms.ValidationError("Please provide a valid Google Drive link")
        
        # Check if we can extract a file ID
        if not Banner.extract_file_id(link):
            raise forms.ValidationError("Could not extract file ID from the provided link")
            
        return link

class LibraryImageForm(forms.ModelForm):
    class Meta:
        model = LibraryImage
        fields = ['google_drive_link']

class HomePageBannerForm(forms.ModelForm):
    class Meta:
        model = HomePageImageBanner
        fields = ['google_drive_link', 'is_active']
        widgets = {
            'google_drive_link': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3})
        }