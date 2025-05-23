# Generated by Django 5.2 on 2025-04-24 23:34

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import shortuuid.django_fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('nfc_id', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('mobile_number', models.CharField(max_length=15)),
                ('emergency_number', models.CharField(max_length=15)),
                ('dob', models.DateField()),
                ('age', models.PositiveIntegerField(blank=True, null=True)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('pincode', models.CharField(max_length=6)),
                ('district', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('education', models.CharField(choices=[('Matriculation', 'Matriculation'), ('Intermediate', 'Intermediate'), ('Diploma', 'Diploma'), ("Bachelor's Degree", "Bachelor's Degree"), ("Master's Degree", "Master's Degree"), ('PhD', 'PhD'), ('Other', 'Other')], max_length=50)),
                ('is_checked_in', models.BooleanField(default=False)),
                ('is_vendor', models.BooleanField(default=False)),
                ('category', models.CharField(choices=[('GEN', 'General'), ('OBC', 'OBC'), ('SC', 'SC'), ('ST', 'ST'), ('PWD', 'PWD'), ('OTHER', 'Others')], default='GEN', help_text='Select your category', max_length=10)),
                ('ssid', shortuuid.django_fields.ShortUUIDField(alphabet=None, blank=True, length=22, max_length=22, null=True, prefix='', unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('vendor_ssids', models.ManyToManyField(blank=True, related_name='staff_members', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.TextField()),
                ('description', models.TextField()),
                ('institution_type', models.CharField(help_text='Type of institution', max_length=100)),
                ('website_url', models.URLField(blank=True, null=True)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_phone', models.CharField(max_length=15)),
                ('capacity', models.PositiveIntegerField(help_text='Maximum capacity of the institution')),
                ('facilities_available', models.TextField(blank=True, help_text='List of available facilities', null=True)),
                ('additional_services', models.TextField(blank=True, help_text='Any additional services offered', null=True)),
                ('is_approved', models.BooleanField(default=False, help_text='Approval status of the application')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_institutions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('description', models.TextField()),
                ('venue_location', models.TextField(help_text='Detailed location of the venue')),
                ('venue_name', models.CharField(help_text='Name of the venue', max_length=200)),
                ('business_type', models.CharField(choices=[('Library', 'Library'), ('Coaching', 'Coaching')], max_length=50)),
                ('social_media_links', models.TextField(blank=True, help_text='Comma separated list of social media links', null=True)),
                ('business_hours', models.CharField(help_text='Operating hours of the business', max_length=100)),
                ('capacity', models.PositiveIntegerField(help_text='Maximum capacity of the venue')),
                ('equipment_available', models.TextField(blank=True, help_text='List of available equipment', null=True)),
                ('additional_services', models.TextField(blank=True, help_text='Any additional services offered', null=True)),
                ('is_approved', models.BooleanField(default=False, help_text='Approval status of the application')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('mobile_number', models.CharField(blank=True, max_length=15, null=True)),
                ('pincode', models.CharField(help_text='Pincode of the venue location', max_length=10)),
                ('district', models.CharField(help_text='District of the venue location', max_length=100)),
                ('city', models.CharField(help_text='City of the venue location', max_length=100)),
                ('state', models.CharField(help_text='State of the venue location', max_length=100)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_libraries', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(blank=True, related_name='joined_libraries', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expense_name', models.CharField(max_length=255)),
                ('expense_description', models.TextField(blank=True, null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('payment_mode', models.CharField(choices=[('CASH', 'Cash'), ('CARD', 'Card'), ('UPI', 'UPI')], default='CASH', max_length=10)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='library.library')),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='library',
            field=models.ManyToManyField(blank=True, related_name='library_users', to='library.library'),
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the subscription plan', max_length=255)),
                ('start_date', models.DateField(help_text='The date when the subscription plan was created')),
                ('duration_in_months', models.IntegerField(help_text='Duration of the subscription plan in months')),
                ('duration_in_hours', models.IntegerField(default=0, help_text='Duration of the subscription plan in hours (if applicable)')),
                ('normal_price', models.DecimalField(decimal_places=2, help_text='The normal price of the subscription plan', max_digits=10)),
                ('discount_price', models.DecimalField(blank=True, decimal_places=2, help_text='The discounted price of the subscription plan (if any)', max_digits=10, null=True)),
                ('library', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscription_plans', to='library.library')),
                ('user', models.ForeignKey(help_text='The vendor who created this subscription plan', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription Plan',
                'verbose_name_plural': 'Subscription Plans',
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], max_length=10)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('valid_from', models.DateTimeField()),
                ('valid_to', models.DateTimeField()),
                ('max_usage', models.PositiveIntegerField(default=1)),
                ('times_used', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_coupons', to=settings.AUTH_USER_MODEL)),
                ('library', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='coupons', to='library.library')),
                ('applicable_plans', models.ManyToManyField(blank=True, to='library.subscriptionplan')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('valid', 'Valid'), ('invalid', 'Invalid')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='library.subscriptionplan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.subscriptionplan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Subscription',
                'verbose_name_plural': 'User Subscriptions',
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in_time', models.DateTimeField(blank=True, null=True)),
                ('check_out_time', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to=settings.AUTH_USER_MODEL)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='library.library')),
            ],
            options={
                'unique_together': {('user', 'library', 'check_in_time')},
            },
        ),
        migrations.CreateModel(
            name='UserVendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_ssid', models.CharField(blank=True, max_length=255)),
                ('vendor_ssid', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_vendor_relationships', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_user_relationships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Vendor Relationship',
                'verbose_name_plural': 'User Vendor Relationships',
                'unique_together': {('user', 'vendor')},
            },
        ),
    ]
