from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Library, SubscriptionPlan, CustomUser, Expense, Coupon, Banner, LibraryImage, HomePageImageBanner, Review, Institution, InstitutionCoupon, InstitutionBanner
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
    opening_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))
    closing_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Library
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

class InstitutionBannerForm(forms.ModelForm):
    class Meta:
        model = InstitutionBanner
        fields = ['google_drive_link']

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

class InstitutionRegistrationForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ['name', 'address', 'pincode', 'state', 'city', 'district', 'description', 'website_url', 
                 'contact_email', 'contact_phone', 'additional_services']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit Postal Code', 'maxlength': '6'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'readonly': 'readonly'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'readonly': 'readonly'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District', 'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Website URL'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact Email'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Phone'}),
            'additional_services': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional Services'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Institution name is required.")
        if len(name) < 3:
            raise forms.ValidationError("Institution name must be at least 3 characters long.")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Description is required.")
        if len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        return description

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode:
            raise forms.ValidationError("Pincode is required.")
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Pincode must be a 6-digit number.")
        return pincode

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        if not email:
            raise forms.ValidationError("Contact email is required.")
        if not '@' in email or not '.' in email:
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone:
            raise forms.ValidationError("Contact phone number is required.")
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError("Phone number must be between 10 and 15 digits.")
        return phone

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise forms.ValidationError("Address is required.")
        if len(address) < 10:
            raise forms.ValidationError("Please provide a complete address.")
        return address

    def clean_website_url(self):
        url = self.cleaned_data.get('website_url')
        if url:  # Website URL is optional
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            if not '.' in url:
                raise forms.ValidationError("Please enter a valid website URL.")
        return url

    def clean(self):
        cleaned_data = super().clean()
        # Add any cross-field validation here if needed
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

class InstitutionCouponForm(forms.ModelForm):
    class Meta:
        model = InstitutionCoupon
        fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 
                 'max_usage', 'status']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'discount_value': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'max_usage': forms.NumberInput(attrs={'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        institution_id = kwargs.pop('institution_id', None)
        super().__init__(*args, **kwargs)
        if institution_id:
            self.fields['code'].validators.append(self.validate_unique_code(institution_id))

    def validate_unique_code(self, institution_id):
        def validator(value):
            if InstitutionCoupon.objects.filter(code=value, institution_id=institution_id).exists():
                raise ValidationError('This coupon code already exists for this institution.')
        return validator

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        discount_value = cleaned_data.get('discount_value')
        discount_type = cleaned_data.get('discount_type')

        if valid_from and valid_to and valid_from >= valid_to:
            raise ValidationError("Valid from date must be before valid to date.")

        if discount_type == 'PERCENTAGE' and discount_value > 100:
            raise ValidationError("Percentage discount cannot be more than 100%.")

        return cleaned_data

class UPIForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ['upi_id', 'recipient_name', 'thank_you_message']
        widgets = {
            'upi_id': forms.TextInput(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out'}),
            'recipient_name': forms.TextInput(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out'}),
            'thank_you_message': forms.Textarea(attrs={'class': 'block w-full rounded-lg border-2 border-gray-200 bg-gray-50 px-5 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-300 transition-all duration-200 ease-in-out', 'rows': 3}),
        }
