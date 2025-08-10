# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, Http404
from django.db.models import Sum, Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin.models import LogEntry
import logging
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db import transaction
from django.views.decorators.http import require_POST
import time

# Set up logging
logger = logging.getLogger(__name__)

# Local imports
from .forms import CustomUserCreationForm, LibraryRegistrationForm, ExpenseForm, UserProfileForm, CouponForm, BannerForm, LibraryImageForm, HomePageBannerForm, ReviewForm
from .models import (
    CustomUser,
    SubscriptionPlan,
    Transaction,
    LibraryAttendance,
    Library,
    Institution,
    UserSubscription,
    Expense,
    Coupon,
    Banner,
    LibraryImage,
    HomePageImageBanner,
    HomePageTextBanner,
    Review,
    VendorSSID,
    AdminCard,
    AdminExpense,
    InstitutionSubscription,
    SubjectFacultyMap,
    TimetableEntry,
    LibraryCardLog,
    InstitutionCardLog,
    Gym,
    GymSubscription,
)
# Python standard library imports
import json
import base64
from io import BytesIO
from datetime import timedelta, datetime
import re

# Third-party imports
import qrcode
from django.views.decorators.http import require_POST, require_GET
from decimal import Decimal
import csv
from collections import defaultdict

User = get_user_model()

def home(request):
    text_banners = HomePageTextBanner.objects.filter(is_active=True)
    image_banners = HomePageImageBanner.objects.filter(is_active=True)
    return render(request, 'users_pages/home.html', {
        'text_banners': text_banners,
        'image_banners': image_banners
    })
def dashboard(request):
    # Get subscriptions for the current user with library details
    active_subscriptions = []
    for subscription in UserSubscription.objects.filter(user=request.user).select_related('subscription__library'):
        # Check if subscription is expired or valid based on end date
        if subscription.end_date and subscription.end_time:
            end_datetime = datetime.combine(subscription.end_date, subscription.end_time)
            end_datetime = timezone.make_aware(end_datetime)
            if end_datetime < timezone.now():
                subscription.status = 'expired'
                subscription.save()
            else:
                subscription.status = 'valid'
                subscription.save()

        # Get latest transaction for this subscription
        latest_transaction = Transaction.objects.filter(
            subscription=subscription.subscription,
            user=request.user
        ).order_by('-created_at').first()
        
        # Determine payment status and color
        if latest_transaction:
            payment_status = latest_transaction.status
            payment_color = 'green' if payment_status == 'valid' else 'yellow' if payment_status == 'pending' else 'red'
            cost = latest_transaction.amount
        else:
            payment_status = 'pending'
            payment_color = 'yellow'
            cost = subscription.subscription.normal_price
            
        # Get library details for this subscription
        library = subscription.subscription.library
        total_seats = library.capacity if library else 0
        available_seats = library.available_seats if library else 0
        
        # Get subscription status
        subscription_status = subscription.status
        status_color = 'green' if subscription_status == 'valid' else 'red'

        subscription_data = {
            'subscription': subscription.subscription,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'start_time': subscription.start_time,
            'end_time': subscription.end_time,
            'cost': cost,
            'subscription_status': {
                'status': subscription_status,
                'color': status_color
            },
            'payment_status': {
                'status': payment_status,
                'color': payment_color
            },
            'library_seats': {
                'total_seats': total_seats,
                'available_seats': available_seats
            }
        }
        active_subscriptions.append(subscription_data)

    # Get institute subscriptions with payment status
    institute_subscriptions = []
    for subscription in InstitutionSubscription.objects.filter(user=request.user).select_related('subscription_plan__institution')[:3]:
        # Use the payment_status directly from the InstitutionSubscription model
        payment_status = subscription.payment_status
        payment_color = 'green' if payment_status == 'valid' else 'yellow' if payment_status == 'pending' else 'red'
        # Check if timetable exists for the institution
        has_timetable = TimetableEntry.objects.filter(institution=subscription.subscription_plan.institution).exists()
        subscription_data = {
            'subscription_plan': subscription.subscription_plan,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'start_time': subscription.start_time,
            'end_time': subscription.end_time,
            'amount_paid': subscription.amount_paid,
            'transaction_id': subscription.transaction_id,
            'status': subscription.status,
            'payment_status': {
                'status': payment_status,
                'color': payment_color
            },
            'coupon_applied': subscription.coupon_applied,
            'has_timetable': has_timetable
        }
        institute_subscriptions.append(subscription_data)

    # Get gym subscriptions for the user
    gym_subscriptions = []
    for sub in GymSubscription.objects.filter(user=request.user).select_related('subscription_plan__gym'):
        plan = sub.subscription_plan
        gym = plan.gym
        payment_status = sub.payment_status
        payment_color = 'green' if payment_status == 'valid' else 'yellow' if payment_status == 'pending' else 'red'
        gym_subscriptions.append({
            'plan': plan,
            'gym': gym,
            'start_date': sub.start_date,
            'end_date': sub.end_date,
            'amount_paid': sub.amount_paid,
            'payment_status': {
                'status': payment_status,
                'color': payment_color
            },
            'status': sub.status,
            'transaction_id': sub.transaction_id,
        })

    context = {
        'active_subscriptions': active_subscriptions,
        'institute_subscriptions': institute_subscriptions,
        'gym_subscriptions': gym_subscriptions,  # <-- add to context
    }
    return render(request, 'users_pages/dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    total_users = CustomUser.objects.count()
    total_libraries = Library.objects.count()
    total_institutions = Institution.objects.count()
    total_gyms = Gym.objects.count()

    approved_libraries = Library.objects.filter(is_approved=True).count()
    approved_institutions = Institution.objects.filter(is_approved=True).count()
    approved_gyms = Gym.objects.filter(is_approved=True).count()
    
    pending_libraries = total_libraries - approved_libraries
    pending_institutions = total_institutions - approved_institutions
    pending_gyms = total_gyms - approved_gyms
    
    # Card allocation stats
    allocated_cards_count = AdminCard.objects.filter(
        Q(library__isnull=False) | Q(institution__isnull=False) | Q(gym__isnull=False)
    ).count()
    non_allocated_cards_count = AdminCard.objects.filter(
        library__isnull=True, institution__isnull=True, gym__isnull=True
    ).count()

    # Get active subscriptions
    active_subscriptions = UserSubscription.objects.filter(
        end_date__gte=timezone.now().date()
    ).count()
    
    # Get recent activities
    recent_activities_count = LogEntry.objects.all().count()
    
    return render(request, 'admin_page/admin_dashboard.html', {
        'total_users': total_users,
        'total_libraries': total_libraries,
        'total_institutions': total_institutions,
        'approved_libraries': approved_libraries,
        'approved_institutions': approved_institutions,
        'approved_gyms': approved_gyms,
        'pending_libraries': pending_libraries,
        'pending_institutions': pending_institutions,
        'pending_gyms': pending_gyms,
        'active_subscriptions': active_subscriptions,
        'recent_activities_count': recent_activities_count,
        'allocated_cards_count': allocated_cards_count,
        'non_allocated_cards_count': non_allocated_cards_count,
        'total_gyms': total_gyms,
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

def user_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.dob = form.cleaned_data['dob']
            user.accepted_terms = form.cleaned_data['terms']
            user.accepted_privacy_policy = form.cleaned_data['privacy']
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/signup.html', {
        'form': form,
        'today': timezone.now().strftime('%Y-%m-%d')
    })

def user_logout(request):
    logout(request)
    return redirect('home')
@login_required
def manage_users(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    # Get users who have subscriptions to this library
    users_with_subscriptions = CustomUser.objects.filter(
        usersubscription__subscription__library=library
    ).distinct()

    # Add subscription status and checkin status to each user
    for user in users_with_subscriptions:
        user.has_active_subscription = UserSubscription.objects.filter(
            user=user,
            subscription__library=library,
            end_date__gte=timezone.now().date()
        ).exists()
        
        # Add checkin status
        user.is_checked_in = LibraryAttendance.objects.filter(
            user=user,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).exists()
    
    return render(request, 'library/manage_users.html', {
        'library': library,
        'users': users_with_subscriptions
    })
@csrf_exempt
def check_access(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            
            if not user_id:
                return JsonResponse({"error": "User ID is required"}, status=400)
            
            user = CustomUser.objects.get(id=user_id)
            
            if not request.user.is_staff:
                return JsonResponse({"error": "Admin not logged in"}, status=403)
            
            subscription = user.subscriptions.order_by('-start_date').first()
            
            if subscription and subscription.is_active():
                transaction = subscription.transactions.first()
                if transaction and transaction.is_valid():
                    return JsonResponse({"access": "granted"})
            
            return JsonResponse({"access": "denied"}, status=403)
            
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def mark_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            library_id = data.get("library_id")
            
            if not nfc_serial or not library_id:
                return JsonResponse({"error": "NFC serial and Library ID are required"}, status=400)
            
            # The CustomUser model does not have an 'nfc_id' field.
            # Instead, we need to look up the user by their LibraryAttendance record with the given nfc_id.
            # We'll find the most recent LibraryAttendance with this nfc_id and get the user from it.
            attendance_with_nfc = LibraryAttendance.objects.filter(nfc_id=nfc_serial).order_by('-check_in_time').first()
            if not attendance_with_nfc:
                return JsonResponse({"error": "User not found for this NFC serial"}, status=404)
            user = attendance_with_nfc.user

            library = Library.objects.get(id=library_id)
            
            # Get current time in IST (UTC+5:30)
            current_time = timezone.now() + timedelta(hours=5, minutes=30)
            active_subscription = UserSubscription.objects.filter(
                user=user,
                subscription__library=library,
                start_date__lte=current_time.date(),
                end_date__gte=current_time.date()
            ).first()

            if not active_subscription:
                return JsonResponse({"error": "User does not have an active subscription"}, status=403)
            
            latest_attendance = LibraryAttendance.objects.filter(
                user=user,
                library=library
            ).order_by('-check_in_time').first()
            
            # Handle time comparisons with date adjustments
            start_time = active_subscription.start_time
            end_time = active_subscription.end_time
            
            # Adjust dates based on time comparison
            if start_time > end_time:
                end_date = active_subscription.start_date + timedelta(days=1)
                start_date = active_subscription.start_date
            else:
                start_date = active_subscription.start_date
                end_date = active_subscription.start_date
            
            # Create datetime objects with adjusted dates
            start_datetime = timezone.make_aware(datetime.combine(
                start_date,
                start_time
            ))
            end_datetime = timezone.make_aware(datetime.combine(
                end_date,
                end_time
            ))
            current_datetime = timezone.make_aware(datetime.combine(
                current_time.date(),
                current_time.time()
            ))
            
            # Check if current time is within allowed period
            is_within_time = (start_datetime <= current_datetime <= end_datetime)
            check_out_color = 0 if is_within_time else 1
            current_time = timezone.now()
            ist_time = current_time + timedelta(hours=5, minutes=30)
            if not latest_attendance or latest_attendance.check_out_time:
                # Check if seats are available
                if library.available_seats <= 0:
                    return JsonResponse({
                        "error": "No seats available",
                        "status": "full"
                    }, status=400)
                
                # New check-in
                attendance = LibraryAttendance.objects.create(
                    user=user,
                    library=library,
                    check_in_time=current_time,
                    check_in_color=check_out_color,
                    check_out_color=0,
                    nfc_id=nfc_serial
                )
                
                # Decrease available seats
                library.available_seats -= 1
                library.save()
                
                return JsonResponse({
                    "message": f"Checked in: {user.get_full_name()}",
                    "action": "checkin",
                    "date": current_time.date().isoformat(),
                    "time": ist_time.strftime("%H:%M:%S"),
                    "available_seats": library.available_seats
                })
            else:
                # Check-out
                latest_attendance.check_out_time = current_time
                latest_attendance.check_out_color = check_out_color
                latest_attendance.save()
                
                # Increase available seats
                library.available_seats += 1
                library.save()
                
                return JsonResponse({
                    "message": f"Checked out: {user.get_full_name()}",
                    "action": "checkout",
                    "date": current_time.date().isoformat(),
                    "time": ist_time.strftime("%H:%M:%S"),
                    "available_seats": library.available_seats
                })
        except Library.DoesNotExist:
            return JsonResponse({"error": "Library not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def confirm_payment(request, plan_id):
    if request.method == 'POST':
        try:
            # Get the subscription plan
            subscription_plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Get user-provided transaction ID and start time
            transaction_id = request.POST.get('transaction_id')
            start_time = request.POST.get('start_time')
            
            # Validate inputs
            if not transaction_id or not start_time:
                messages.error(request, "Transaction ID and Start Time are required")
                return redirect('payment', plan_id=plan_id)
            
            # Check if transaction ID already exists
            if Transaction.objects.filter(transaction_id=transaction_id).exists():
                messages.error(request, "Transaction ID already exists")
                return redirect('payment', plan_id=plan_id)
            
            # Get the final price from the session
            final_price = Decimal(request.session.get('final_price', subscription_plan.normal_price))
            
            # Create transaction record
            transaction = Transaction.objects.create(
                user=request.user,
                subscription=subscription_plan,
                transaction_id=transaction_id,
                amount=final_price,
                status='pending'
            )
            
            # Calculate end time based on duration in hours
            start_datetime = datetime.combine(timezone.now().date(), 
                                            datetime.strptime(start_time, '%H:%M').time())
            end_datetime = start_datetime + timedelta(hours=subscription_plan.duration_in_hours)
            
            # Create UserSubscription record with time
            UserSubscription.objects.create(
                user=request.user,
                subscription=subscription_plan,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=subscription_plan.duration_in_months * 30),
                start_time=start_time,
                end_time=end_datetime.time()
            )
            
            # Clear the session data
            if 'final_price' in request.session:
                del request.session['final_price']

            return redirect('payment_confirmation', transaction_id=transaction.transaction_id)
            
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Subscription plan not found")
            return redirect('payment', plan_id=plan_id)
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('payment', plan_id=plan_id)
    
    return redirect('home')

@login_required
def payment_success(request, transaction_id):
    # Fetch the transaction details
    transaction = Transaction.objects.get(transaction_id=transaction_id)
    return render(request, 'users_pages/payment_confirmation.html', {
        'transaction_id': transaction.transaction_id,
        'subscription_id': transaction.subscription.id,
        'status': transaction.status
    })

@login_required
def payment_confirmation(request, transaction_id):
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id, user=request.user)
        return render(request, 'users_pages/payment_confirmation.html', {
            'transaction_id': transaction.transaction_id,
            'subscription_id': transaction.subscription.id,
            'status': transaction.status
        })
    except Transaction.DoesNotExist:
        messages.error(request, "Transaction not found")
        return redirect('home')

@login_required
def all_attendance(request, vendor_id):
    # Get the library/vendor
    library = get_object_or_404(Library, id=vendor_id)
    
    # Get all attendance records for this library
    attendances = LibraryAttendance.objects.filter(library=library).order_by('-check_in_time')
      # This ensures page_obj is always defined
    
    # Add search functionality
    search_query = request.GET.get('search')
    if search_query:
        attendances = attendances.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Calculate duration for each attendance
    for attendance in attendances:
        if attendance.check_in_time and attendance.check_out_time:
            duration = attendance.check_out_time - attendance.check_in_time
            total_seconds = duration.total_seconds()
            
            # Find active subscription
            subscription = UserSubscription.objects.filter(
                user=attendance.user,
                subscription__library=library,
                start_date__lte=attendance.check_in_time.date(),
                end_date__gte=attendance.check_in_time.date()
            ).first()
            
            if subscription:
                subscription_duration = subscription.subscription.duration_in_hours * 3600
                # Set duration_color to 1 if exceeded, 0 if within limit
                attendance.duration_color = 1 if total_seconds > subscription_duration else 0
            
            # Format duration string correctly
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            attendance.duration = f"{hours:02d}h:{minutes:02d}m:{seconds:02d}s"
        else:
            attendance.duration = "00h:00m:00s"
            attendance.duration_color = 0
            
    paginator = Paginator(attendances, 25)  # Show 25 attendances per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/all_attendence.html', {
        'attendances': page_obj,
        'library': library
    })

@login_required
def expense_dashboard(request, library_id):
    if not request.user.is_authenticated:
        return redirect('login')
    library = get_object_or_404(Library, id=library_id)

    # Get date filters from request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Base querysets
    transactions = Transaction.objects.filter(subscription__library=library)
    expenses = Expense.objects.filter(library=library)
    
    
    
    # Calculate totals
    total_earnings = transactions.aggregate(total=Sum('amount'))['total'] or 0
    valid_amount = transactions.filter(status='valid').aggregate(total=Sum('amount'))['total'] or 0
    invalid_amount = transactions.filter(status='invalid').aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_profit = float(valid_amount) - float(total_expenses)
    valid_transection = transactions.filter(status='valid').select_related('user', 'subscription').order_by('-created_at')

    # Apply date filters if provided
    if from_date and to_date:
        adjusted_from_date = (timezone.datetime.strptime(from_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        adjusted_to_date = (timezone.datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        transactions = transactions.filter(created_at__range=[from_date, to_date])
        expenses = expenses.filter(date__range=[from_date, to_date])
        valid_transection = valid_transection.filter(created_at__range=[adjusted_from_date, adjusted_to_date])
        
        

    
    context = {
        'library': library,
        'total_earnings': total_earnings,
        'valid_amount': valid_amount,
        'invalid_amount': invalid_amount,
        'expenses': expenses.order_by('-date')[:10],
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'valid_transactions': valid_transection,
        'from_date': from_date,
        'to_date': to_date,
    }
    
    return render(request, 'library/expense.html', context)

@login_required
def add_expense(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            try:
                expense = form.save(commit=False)
                expense.library = library
                expense.save()
                messages.success(request, "Expense added successfully")
            except Exception as e:
                messages.error(request, f"Error adding expense: {str(e)}")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('expense_dashboard', library_id=library_id)

def vender_type(request):
    """Render the vendor type selection page"""
    return render(request, 'vender/vender_type.html')

@login_required
def register_library(request):
    if request.method == 'POST':
        form = LibraryRegistrationForm(request.POST)
        if form.is_valid():
            library = form.save(commit=False)
            library.owner = request.user
            library.user = request.user
            library.business_type = 'Library'
            library.save()
            messages.success(request, "Library registered successfully!")
            return redirect('dashboard')
    else:
        form = LibraryRegistrationForm()
    
    return render(request, 'vender/register_library.html', {'form': form})

def register_venders_shop(request):
    if not request.user.is_authenticated:
        return redirect('login')
    query = request.GET.get('q', '')
    libraries = Library.objects.filter(Q(venue_name__icontains=query) |
                                        Q(address__icontains=query) |
                                        Q(city__icontains=query) |
                                        Q(state__icontains=query) |
                                        Q(district__icontains=query) |
                                        Q(pincode__icontains=query))
    
    items = list(libraries) if libraries.exists() else Library.objects.all()
    return render(request, 'users_pages/register_venders_shop.html', {'items': items})
def register_institute(request):
    if not request.user.is_authenticated:
        return redirect('login')
    query = request.GET.get('q', '')
    institutions = Institution.objects.filter(
        Q(name__icontains=query) | 
        Q(address__icontains=query) | 
        Q(contact_email__icontains=query) | 
        Q(contact_phone__icontains=query) | 
        Q(website_url__icontains=query) |
        Q(pincode__icontains=query)
    )
    items = list(institutions)
    
    return render(request, 'users_pages/register_institute.html', {'items': items})

@login_required
def admin_library_details(request, library_id):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page")
    
    library = get_object_or_404(Library, id=library_id)
    return render(request, 'admin_page/admin_library_details.html', {
        'library': library,
    })

@login_required
def public_library_details(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if not request.user.is_authenticated:
        return redirect('login')
    library = get_object_or_404(Library, id=library_id)
    if not library.is_approved:
        raise Http404("Library not found")
    banners = library.banners.order_by('-created_at')
    recent_reviews = library.reviews.all().order_by('-created_at')[:2]
    
    # Calculate average rating with 2 decimal places
    average_rating = round(library.average_rating(), 2)
    has_active_subscription = False
    has_reviewed = False

    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(library=library, user=request.user).exists()
        has_active_subscription = UserSubscription.objects.filter(
            user=request.user,
            subscription__library=library,
            end_date__gte=timezone.now().date()
        ).exists()

    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(library=library, user=request.user).exists()
    
    return render(request, 'library/library_details.html', {
        'library': library,
        'banners': banners,
        'recent_reviews': recent_reviews,
        'has_reviewed': has_reviewed,
        'average_rating': average_rating,
        'has_active_subscription': has_active_subscription

    })

@login_required
def enroll_library(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.method == 'POST':
        # Add user to library
        library.users.add(request.user)
        return redirect('subscription_page', vendor_id=library.owner.id)
    
    return render(request, 'library/enroll_library.html', {'library': library})

def enrollment_success(request):
    return render(request, 'library/enrollment_success.html')

@login_required
def library_dashboard(request, library_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    library = get_object_or_404(Library, id=library_id)
    total_seats = library.capacity if library else 0
    available_seats = library.available_seats if library else 0
    
    # Get unique users who have active subscriptions
    active_users = UserSubscription.objects.filter(
        subscription__library=library,
        end_date__gte=timezone.now().date()
    ).values('user').distinct().count()
    
    # Get total active subscriptions
    active_subscriptions_count = UserSubscription.objects.filter(
        subscription__library=library,
        end_date__gte=timezone.now().date()
    ).count()
    
    # Get all subscription plans
    plans = SubscriptionPlan.objects.filter(library=library)
    
    # Prepare plans data with library-specific UPI details
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'normal_price': plan.normal_price,
            'discount_price': plan.discount_price,
            'has_discount': plan.has_discount,
            'upi_id': library.upi_id,
            'recipient_name': library.recipient_name,
            'thank_you_message': library.thank_you_message
        })
    
    upidata = {
        "upi_id": library.upi_id,
        "recipient_name": library.recipient_name,
        "thank_you_message": library.thank_you_message,
    }
    

    return render(request, 'library/library_dashboard.html', {
        'library': library,
        'plans': plans_data,
        'user_count': active_users,
        'active_subscriptions_count': active_subscriptions_count,
        'upidata': upidata,
        'total_seats': total_seats,
        'available_seats': available_seats
    })

@login_required
def subscription_page(request, library_id):
    if not request.user.is_authenticated:
        return redirect('login')
    library = get_object_or_404(Library, id=library_id)
    vendor = library.owner
    
    subscription_plans = SubscriptionPlan.objects.filter(
        user=vendor,
        library=library
    )
    
    # Calculate percentage difference for each plan
    plans_with_discount = []
    for plan in subscription_plans:
        if plan.discount_price and plan.normal_price:
            discount_amount = plan.normal_price - plan.discount_price
            percentage_difference = (discount_amount / plan.normal_price) * 100
            plan.percentage_difference = round(percentage_difference, 2)
        else:
            plan.percentage_difference = 0
        plans_with_discount.append(plan)
    
    context = {
        'vendor': vendor,
        'library': library,
        'subscription_plans': plans_with_discount
    }
    
    return render(request, 'library/subscription_page.html', context)

@login_required
def manage_libraries(request):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page")
    
    libraries = Library.objects.all().select_related('owner')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'approved':
        libraries = libraries.filter(is_approved=True)
    elif status == 'unapproved':
        libraries = libraries.filter(is_approved=False)
    
    # Search by name or owner
    search_query = request.GET.get('search')
    if search_query:
        libraries = libraries.filter(
            Q(venue_name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(pincode__icontains=search_query)
        )
    
    return render(request, 'admin_page/manage_libraries.html', {
        'libraries': libraries,
        'status': status,
        'search_query': search_query
    })

@login_required
def toggle_library_approval(request, library_id):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to perform this action")
    
    library = get_object_or_404(Library, id=library_id)
    library.is_approved = not library.is_approved
    library.save()
    return redirect('manage_libraries')

@login_required
def manage_institutions(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page")
    
    institutions = Institution.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'approved':
        institutions = institutions.filter(is_approved=True)
    elif status == 'unapproved':
        institutions = institutions.filter(is_approved=False)
    
    # Search by name or owner
    search_query = request.GET.get('search')
    if search_query:
        institutions = institutions.filter(
            Q(name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query)
        )
    
    return render(request, 'admin_page/manage_institutions.html', {
        'institutions': institutions,
    })

@login_required
def create_subscription(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to create plans for this library")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        normal_price = request.POST.get('normal_price')
        discount_price = request.POST.get('discount_price') or None
        duration_in_months = request.POST.get('duration_in_months')
        duration_in_hours = request.POST.get('duration_in_hours')
        start_date = timezone.now().date()
        
        if not all([name, normal_price, duration_in_months, duration_in_hours]):
            messages.error(request, "Please fill in all required fields")
            return redirect('create_subscription', library_id=library.id)
        
        try:
            SubscriptionPlan.objects.create(
                user=request.user,
                library=library,
                name=name,
                normal_price=normal_price,
                discount_price=discount_price,
                duration_in_months=duration_in_months,
                duration_in_hours=duration_in_hours,
                start_date=start_date
            )
            messages.success(request, "Subscription plan created successfully!")
            return redirect('library_dashboard', library_id=library.id)
        except Exception as e:
            messages.error(request, f"Error creating plan: {str(e)}")
            return redirect('create_subscription', library_id=library.id)
    
    return render(request, 'library/create_subscription.html', {
        'library': library
    })

@login_required
def payment_page(request, plan_id):
    # Get the subscription plan and user's library
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    library = plan.library
    
    # Process coupon code from request
    coupon_code = request.GET.get('coupon')
    if coupon_code and '?coupon=' in coupon_code:
        coupon_code = coupon_code.split('?coupon=')[0]
    
    # Initialize coupon and pricing variables
    coupon = None
    discount_applied = False
    final_price = plan.discount_price if plan.has_discount else plan.normal_price
    original_price = final_price
    
    # Validate and apply coupon if provided
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid() and plan in coupon.applicable_plans.all():
                final_price = coupon.apply_discount(final_price)
                discount_applied = True
        except Coupon.DoesNotExist:
            pass

    if discount_applied:
        coupon.increment_usage()
    
    # Calculate discount amount
    discount_amount = float(original_price) - float(final_price) if discount_applied else 0
    
    # Store final price in session
    request.session['final_price'] = str(final_price)
    
    # Prepare UPI payment details
    upi_id = library.upi_id
    recipient_name = library.recipient_name
    thank_you_message = library.thank_you_message
    # Generate a timestamp for the transaction reference
    timestamp = int(time.time())
    tr = f"{timestamp}"
    # Generate UPI payment link with timestamp in 'tr'
    upi_link = f"upi://pay?pa={upi_id}&pn={recipient_name}&mc=1234&tid=transaction123&tr={tr}&tn={thank_you_message}&am={final_price}&cu=INR"
    # Create QR code for UPI payment
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Prepare context for template
    context = {
        'plan': plan,
        'final_price': final_price,
        'qr_code': qr_code,
        'coupon': coupon,
        'discount_applied': discount_applied,
        'upi_id': upi_id,
        'recipient_name': recipient_name,
        'discount_amount': discount_amount
    }

    return render(request, 'users_pages/payment.html', context)

@login_required
def user_subscriptions(request):
    # Get all subscriptions for the user, ordered by end date
    subscriptions = UserSubscription.objects.filter(
        user=request.user
    ).select_related('subscription').order_by('-end_date')

    # Get latest transaction for each subscription
    for subscription in subscriptions:
        latest_transaction = Transaction.objects.filter(
            user=request.user,
            subscription=subscription.subscription
        ).order_by('-created_at').first()
        
        # Use the existing status field from UserSubscription model
        if subscription.status == 'expired':
            status_color = 'red'
        else:
            status_color = 'green'
        # Determine payment status
        subscription.latest_transaction = latest_transaction
        subscription.payment_status = {
            'status': latest_transaction.status if latest_transaction else None,
            'subscription_status': subscription.status,
            'subscription_status_color': status_color,
            'color': 'green' if latest_transaction and latest_transaction.status == 'valid' else 
                    'yellow' if latest_transaction and latest_transaction.status == 'pending' else 
                    'red'
        }
        subscription.cost = latest_transaction.amount if latest_transaction else subscription.subscription.normal_price

    context = {
        'subscriptions': subscriptions
    }
    return render(request, 'users_pages/user_subscriptions.html', context)

@login_required
def verify_payments(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    transactions = Transaction.objects.filter(
        subscription__library=library
    ).select_related('user', 'subscription').order_by('-created_at')
    
    status = request.GET.get('status')
    if status and status != 'all':
        transactions = transactions.filter(status=status)
    
    search_query = request.GET.get('search')
    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(subscription__name__icontains=search_query)
        )
    
    context = {
        'library': library,
        'transactions': transactions,
        'status_filter': status
    }
    return render(request, 'library/verify_payments.html', context)

@login_required
def verify_single_payment(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        # Update transaction status
        transaction.status = 'valid'
        transaction.save()
        
        # Create or update user subscription
        user_subscription, created = UserSubscription.objects.update_or_create(
            user=transaction.user,
            subscription=transaction.subscription,
            defaults={
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=transaction.subscription.duration_in_months * 30)
            }
        )
        user_subscription.transactions.add(transaction)
        
        messages.success(request, "Payment successfully verified")
        return redirect('verify_payments', library_id=transaction.subscription.library.id)
    
    messages.error(request, "Invalid request method")
    return redirect('verify_payments', library_id=transaction.subscription.library.id)

@login_required
def update_transaction_status(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Transaction.STATUS_CHOICES).keys():
            transaction.status = new_status
            transaction.save()
            messages.success(request, f"Transaction status updated to {new_status}")
        else:
            messages.error(request, "Invalid status selected")
    
    return redirect('verify_payments', library_id=transaction.subscription.library.id)

@login_required
def edit_library_profile(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.method == 'POST':
        # Get the new capacity value
        new_capacity = int(request.POST.get('capacity'))
        old_capacity = library.capacity
        
        # Calculate the difference between new and old capacity
        capacity_diff = new_capacity - old_capacity
        
        # Update available seats based on capacity change
        if capacity_diff > 0:
            library.available_seats += capacity_diff
        elif capacity_diff < 0:
            library.available_seats += capacity_diff
        
        # Only update allowed fields
        library.address = request.POST.get('address')
        library.description = request.POST.get('description')
        library.venue_location = request.POST.get('venue_location')
        library.venue_name = request.POST.get('venue_name')
        library.social_media_links = request.POST.get('social_media_links')
        library.capacity = request.POST.get('capacity')
        library.opening_time = request.POST.get('opening_time')
        library.closing_time = request.POST.get('closing_time')
        library.equipment_available = request.POST.get('equipment_available')
        library.additional_services = request.POST.get('additional_services')
        library.pincode = request.POST.get('pincode')
        library.district = request.POST.get('district')
        library.city = request.POST.get('city')
        library.state = request.POST.get('state')
        library.save()
        messages.success(request, 'Library profile updated successfully!')
        return redirect('library_dashboard', library_id=library.id)
    
    return render(request, 'library/edit_library_profile.html', {'form': library})

@login_required
@csrf_exempt
def allocate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            user_id = data.get("user_id")
            library_id = data.get("library_id")

            if not nfc_serial or not user_id or not library_id:
                return JsonResponse({'error': 'NFC serial, user ID, and library ID are required'}, status=400)

            # Check if card exists and is allocated to this library
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'This card is not registered in the system'}, status=400)
            if card.library is None:
                return JsonResponse({'error': 'This card is not yet allocated to any library'}, status=400)
            if card.library.id != int(library_id):
                return JsonResponse({'error': 'This card is allocated to a different library'}, status=400)
            # If we reach here, card is allocated to this library, so allow allocation to user

            # Check if user already has a card (by mapping)
            if LibraryCardLog.objects.filter(user_id=user_id, library_id=library_id, card_id=nfc_serial).exists():
                return JsonResponse({'error': 'This user already has this card allocated in this library'}, status=400)

            user = CustomUser.objects.get(id=user_id)
            library = Library.objects.get(id=library_id)

            # Allocate card (create the mapping)
            with transaction.atomic():
                LibraryCardLog.objects.create(
                    library=library,
                    user=user,
                    card_id=nfc_serial,
                    allocated_by=request.user
                )
            return JsonResponse({
                'success': True,
                'message': 'User activated successfully',
                'user': {
                    'id': user.id,
                    'name': user.get_full_name(),
                    'mobile': user.mobile_number
                }
            })
        except Exception as e:
            logger.error(f"Error in allocate function: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def deallocate_nfc(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            if not nfc_serial:
                return JsonResponse({'error': 'NFC serial is required'}, status=400)
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'No card found with this NFC ID'}, status=404)
            if card.library is None:
                return JsonResponse({'error': 'This card is not allocated to any library'}, status=400)

            # Find the user to deallocate (latest mapping)
            last_log = LibraryCardLog.objects.filter(card_id=nfc_serial, library=card.library).order_by('-timestamp').first()
            user_to_deallocate = last_log.user if last_log else None

            # Remove the mapping (delete the entry)
            if user_to_deallocate:
                LibraryCardLog.objects.filter(library=card.library, user=user_to_deallocate, card_id=nfc_serial).delete()
            return JsonResponse({'success': True, 'message': 'NFC ID deallocated successfully'})
        except Exception as e:
            logger.error(f"Error in deallocate_nfc function: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def nfc_add_user_page(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    # Get all users who have ever subscribed to this library
    enrolled_user_ids = UserSubscription.objects.filter(
        subscription__library=library
    ).values_list('user_id', flat=True).distinct()
    users = CustomUser.objects.filter(id__in=enrolled_user_ids)
    # Annotate each user with has_card
    user_ids_with_cards = set(LibraryCardLog.objects.filter(library=library).values_list('user_id', flat=True))
    users_with_status = []
    for user in users:
        users_with_status.append({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile_number': user.mobile_number,
            'has_card': user.id in user_ids_with_cards
        })
    return render(request, 'library/nfc_add_user.html', {
        'library': library,
        'users': users_with_status
    })

@login_required
def attendance_page(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    return render(request, 'library/attendance_page.html', {'library': library})

@login_required
@csrf_exempt
def check_nfc_allocation(request):
    def is_card_allocated_to_library(nfc_serial, library_id):
        try:
            card = AdminCard.objects.get(card_id=nfc_serial)
            # Accept both int and str for library_id
            if card.library and str(card.library.id) == str(library_id):
                return True
            return False
        except AdminCard.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking card allocation: {str(e)}")
            return False

    if request.method == 'POST':
        try:
            # Validate content type
            if request.content_type != 'application/json':
                return JsonResponse(
                    {'error': 'Invalid content type, expected application/json'}, 
                    status=400,
                    content_type='application/json'
                )
            # Parse and validate data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Invalid JSON data'}, 
                    status=400,
                    content_type='application/json'
                )
            nfc_serial = data.get('nfc_serial')
            library_id = data.get('library_id')
            if not nfc_serial or not isinstance(nfc_serial, str):
                return JsonResponse(
                    {'error': 'Valid NFC serial is required'}, 
                    status=400,
                    content_type='application/json'
                )
            if not library_id:
                return JsonResponse(
                    {'error': 'Library ID is required'}, 
                    status=400,
                    content_type='application/json'
                )
            # Check if NFC card is allocated to this library using helper function
            if not is_card_allocated_to_library(nfc_serial, library_id):
                return JsonResponse(
                    {'error': 'This card is not allocated to this library or coaching'}, 
                    status=400,
                    content_type='application/json'
                )
            # Query database
            # CustomUser does not have nfc_id, so use Attendance to find the user with this nfc_serial
            # Check LibraryCardLog to find user associated with this NFC serial
            card_log = LibraryCardLog.objects.filter(card_id=nfc_serial).order_by('-timestamp').first()
            user = card_log.user if card_log else None
            response_data = {
                'allocated': bool(user),
                'nfcid': nfc_serial,
                'timestamp': timezone.now().isoformat()
            }
            if user:
                response_data.update({
                    'user_full_name': user.get_full_name(),
                    'user_mobile': user.mobile_number,
                    'user_id': user.id
                })
            return JsonResponse(
                response_data,
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"Error checking NFC allocation: {str(e)}", exc_info=True)
            return JsonResponse(
                {
                    'error': 'An error occurred while processing your request',
                    'error_details': str(e)
                }, 
                status=500,
                content_type='application/json'
            )
    return JsonResponse(
        {'error': 'Invalid request method'}, 
        status=405,
        content_type='application/json'
    )

def terms_conditions(request):
    return render(request, 'conditions_and_policy/terms_conditions.html')

def privacy_policy(request):
    return render(request, 'conditions_and_policy/privacy_policy.html')

def cookies_policy(request):
    return render(request, 'conditions_and_policy/cookies_policy.html')

def disclaimer(request):
    return render(request, 'conditions_and_policy/disclaimer.html')

@login_required
def staff_management(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    staff_members = library.staff.all()
    
    # Get VendorSSID permissions for each staff member
    staff_data = []
    for staff in staff_members:
        vendor_ssid = VendorSSID.objects.filter(user=staff, library=library).first()
        permissions = vendor_ssid.permissions.split(',') if vendor_ssid and vendor_ssid.permissions else []
        staff_data.append({
            'staff': staff,
            'permissions': permissions
        })
    
    return render(request, 'library/staff_management.html', {
        'library': library,
        'staff_members': staff_members,
        'staff_data': staff_data

    })

@login_required
def add_staff(request, library_id):
    if request.method == 'POST':
        library = get_object_or_404(Library, id=library_id)
        
        # Ensure only the library owner can add staff
        if request.user != library.owner:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        ssid = request.POST.get('ssid')
        permissions = request.POST.getlist('permissions[]')  # Get selected permissions
        
        if not ssid:
            return JsonResponse({'success': False, 'message': 'SSID is required'}, status=400)
        
        try:
            user = CustomUser.objects.get(ssid=ssid)
            
            # Check if user is already a staff member
            if user in library.staff.all():
                return JsonResponse({'success': False, 'message': 'User is already a staff member'})
            
            # Add user to staff and update vendor relationship
            library.staff.add(user)
            
            # Store vendor's SSID and permissions in the user's vendor_ssids field
            if not user.vendor_ssids:
                user.vendor_ssids = f"{request.user.ssid}:{','.join(permissions)}"
            else:
                user.vendor_ssids += f",{request.user.ssid}:{','.join(permissions)}"
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{user.get_full_name()} added as staff',
                'user': {
                    'full_name': user.get_full_name(),
                    'ssid': user.ssid,
                    'permissions': permissions
                }
            })
            
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User with this SSID not found'}, status=404)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
def get_staff(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.user != library.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    staff = library.staff.all()
    staff_data = [{
        'full_name': user.get_full_name(),
        'ssid': user.ssid
    } for user in staff]
    
    return JsonResponse({'staff': staff_data})

@login_required
def search_user(request):
    query = request.GET.get('query', '')
    if len(query) < 3:
        return JsonResponse({'users': []})

    users = CustomUser.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(ssid__iexact=query)
    ).values('id', 'first_name', 'last_name', 'email')[:10]

    user_list = [
        {
            'id': user['id'],
            'full_name': f"{user['first_name']} {user['last_name']}",
            'email': user['email']
        }
        for user in users
    ]

    return JsonResponse({'users': user_list})

@login_required
def all_users(request):
    users = CustomUser.objects.all()
    return render(request, 'admin_page/all_users.html', {'users': users})

@login_required
def all_libraries(request):
    libraries = Library.objects.all()
    return render(request, 'admin_page/all_libraries.html', {'libraries': libraries})

@login_required
def user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin_page/user_details.html', {
        'user': user,
    })

@login_required
def admin_full_info_library_details(request, library_id):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page")
    
    try:
        library = Library.objects.get(id=library_id)
        return render(request, 'admin_page/library_details.html', {'library': library})
    except Library.DoesNotExist:
        raise Http404("Library not found")

def apply_for_vendor(request):
    """Redirect to the vendor type selection page"""
    return render(request, 'vender/vender_type.html')

@login_required
def manage_subscriptions(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    # Check if the user is the owner
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to manage subscriptions for this library")
    
    subscriptions = SubscriptionPlan.objects.filter(library=library)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        subscription_id = request.POST.get('subscription_id')
        
        if action == 'delete':
            try:
                subscription = SubscriptionPlan.objects.get(id=subscription_id, library=library)
                subscription.delete()
                messages.success(request, "Subscription deleted successfully!")
            except SubscriptionPlan.DoesNotExist:
                messages.error(request, "Subscription not found")
        
        elif action == 'edit':
            try:
                subscription = SubscriptionPlan.objects.get(id=subscription_id, library=library)
                subscription.name = request.POST.get('name')
                subscription.duration_in_months = int(request.POST.get('duration_in_months', 0))
                subscription.duration_in_hours = int(request.POST.get('duration_in_hours', 0))
                subscription.cost = float(request.POST.get('cost', 0))
                subscription.save()
                messages.success(request, "Subscription updated successfully!")
            except (SubscriptionPlan.DoesNotExist, ValueError) as e:
                messages.error(request, f"Error updating subscription: {str(e)}")
    
    return render(request, 'library/manage_subscriptions.html', {
        'library': library,
        'subscriptions': subscriptions
    })

@login_required
@csrf_exempt
def deallocate_nfc(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            if not nfc_serial:
                return JsonResponse({'error': 'NFC serial is required'}, status=400)
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'No card found with this NFC ID'}, status=404)
            if card.library is None:
                return JsonResponse({'error': 'This card is not allocated to any library'}, status=400)

            # Find the user to deallocate (latest mapping)
            last_log = LibraryCardLog.objects.filter(card_id=nfc_serial, library=card.library).order_by('-timestamp').first()
            user_to_deallocate = last_log.user if last_log else None

            # Remove the mapping (delete the entry)
            if user_to_deallocate:
                LibraryCardLog.objects.filter(library=card.library, user=user_to_deallocate, card_id=nfc_serial).delete()
            return JsonResponse({'success': True, 'message': 'NFC ID deallocated successfully'})
        except Exception as e:
            logger.error(f"Error in deallocate_nfc function: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def expense_chart(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to edit this library profile")
    
    # Get filter parameters
    period = request.GET.get('period')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Initialize date range
    start_date = None
    end_date = None
    
    # Set date range based on period if provided
    if period:
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
    elif from_date and to_date:
        start_date = from_date
        end_date = to_date

    # Get expenses and transactions data
    expenses = Expense.objects.filter(library=library)
    transactions = Transaction.objects.filter(subscription__library=library)
    
    # Apply date filters if provided
    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])
        transactions = transactions.filter(created_at__range=[start_date, end_date])
    
    # Calculate transaction data
    total_earnings = float(transactions.aggregate(total=Sum('amount'))['total'] or 0)
    valid_transactions = float(transactions.filter(status='valid').aggregate(total=Sum('amount'))['total'] or 0)
    invalid_transactions = float(transactions.filter(status='invalid').aggregate(total=Sum('amount'))['total'] or 0)
    total_expenses = float(expenses.aggregate(total=Sum('amount'))['total'] or 0)
    total_profit = valid_transactions - total_expenses

    # Prepare data for charts
    expense_data = expenses.values('expense_name').annotate(total=Sum('amount'))
    expense_categories = [item['expense_name'] for item in expense_data]
    expense_amounts = [float(item['total']) for item in expense_data]
    
    # Prepare data for line chart
    date_data = expenses.values('date').annotate(total=Sum('amount')).order_by('date')
    date_labels = [item['date'].strftime('%Y-%m-%d') for item in date_data]
    date_amounts = [float(item['total']) for item in date_data]

    # Prepare pie chart data
    pie_data = {
        'labels': ['Total Expenses', 'Valid Transactions', 'Invalid Transactions'],
        'values': [total_expenses, valid_transactions, invalid_transactions]
    }

    # Prepare profit data
    profit_data = transactions.values('created_at__date').annotate(
        income=Sum('amount', filter=Q(status='valid')),
        expense=Sum('amount', filter=Q(status='invalid'))
    ).order_by('created_at__date')
    
    profit_labels = [item['created_at__date'].strftime('%Y-%m-%d') for item in profit_data]
    profit_values = [float(item['income'] or 0) - float(item['expense'] or 0) for item in profit_data]
    

    context = {
        'library': library,
        'total_earnings': total_earnings,
        'valid_transactions': valid_transactions,
        'invalid_transactions': invalid_transactions,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'expense_categories': json.dumps(expense_categories),
        'expense_amounts': json.dumps(expense_amounts),
        'date_labels': json.dumps(date_labels),
        'date_amounts': json.dumps(date_amounts),
        'pie_data': json.dumps(pie_data),
        'profit_labels': json.dumps(profit_labels),
        'profit_values': json.dumps(profit_values),
        'from_date': from_date,
        'to_date': to_date,
    }
    
    return render(request, 'library/expense_charts.html', context)

@login_required
def edit_expense(request, library_id, expense_id):
    library = get_object_or_404(Library, id=library_id)
    expense = get_object_or_404(Expense, id=expense_id, library=library)
    
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to edit this expense")
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated successfully")
            return redirect('expense_dashboard', library_id=library_id)
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'library': library,
        'expense': expense
    }
    return render(request, 'library/edit_expense.html', context)

@login_required
def delete_expense(request, library_id, expense_id):
    library = get_object_or_404(Library, id=library_id)
    expense = get_object_or_404(Expense, id=expense_id, library=library)
    
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to delete this expense")
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense deleted successfully")
        return redirect('expense_dashboard', library_id=library_id)
    
    return redirect('expense_dashboard', library_id=library_id)

@login_required
def user_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'authentication/profile.html', {'user': user})

@login_required
def update_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        # Only update allowed fields
        user.emergency_number = request.POST.get('emergency_number')
        user.address = request.POST.get('address')
        user.pincode = request.POST.get('pincode')
        user.category = request.POST.get('category')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile', user_id=user.id)
    
    return render(request, 'authentication/update_profile.html', {'user': user})

@login_required
def create_coupon(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, library_id=library_id)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.library = library
            coupon.created_by = request.user
            
            # Handle "All Plans" selection
            if 'all' in form.cleaned_data['applicable_plans']:
                coupon.applicable_plans.set(SubscriptionPlan.objects.filter(library=library))
            else:
                coupon.save()
                form.save_m2m()
            
            messages.success(request, "Coupon created successfully!")
            return redirect('library_dashboard', library_id=library.id)
        else:
            # If form is invalid, show error messages
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CouponForm(library_id=library_id)
    
    return render(request, 'library/create_coupon.html', {
        'library': library,
        'form': form
    })

@login_required
def manage_coupons(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    coupons = Coupon.objects.filter(library=library)
    return render(request, 'library/manage_coupons.html', {'coupons': coupons, 'library': library})

@csrf_exempt
@require_POST
def apply_coupon(request):
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')
        library_id = data.get('library_id')
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Coupon code is required'
            }, status=400)

        if not library_id:
            return JsonResponse({
                'success': False,
                'message': 'Library ID is required'
            }, status=400)

        coupon = Coupon.objects.get(code=coupon_code, library_id=library_id)

        if not coupon.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Coupon is not active'
            })

        if not coupon.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Coupon is not valid'
            })

        applicable_plans = coupon.applicable_plans.all()
        
        if not applicable_plans.exists():
            applicable_plans = SubscriptionPlan.objects.filter(library_id=library_id)

        discounted_plans = []

        for plan in applicable_plans:
            # Use discount_price if available, otherwise use normal_price
            base_price = plan.discount_price if plan.has_discount else plan.normal_price
            
            if coupon.discount_type == 'percentage':
                discount_amount = base_price * (coupon.discount_value / 100)
            else:
                discount_amount = coupon.discount_value

            discounted_price = max(base_price - discount_amount, 0)
            discounted_plans.append({
                'id': plan.id,
                'original_price': str(base_price),
                'discounted_price': str(discounted_price)
            })

        return JsonResponse({
            'success': True,
            'message': 'Coupon applied successfully',
            'discounted_plans': discounted_plans,
            'coupon_id': coupon.id
        })

    except Coupon.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid coupon code'
        }, status=404)
    except Exception as e:
        logger.error(f"Error applying coupon: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while applying coupon: {str(e)}'
        }, status=500)

@login_required
@require_POST
def edit_subscription(request):
    try:
        subscription_id = request.POST.get('id')
        if not subscription_id:
            messages.error(request, 'Subscription ID is required')
            return redirect('manage_subscriptions', library_id=request.POST.get('library_id'))

        subscription = SubscriptionPlan.objects.get(id=subscription_id)
        
        # Validate and update fields
        name = request.POST.get('name')
        duration_months = request.POST.get('duration_in_months')
        duration_hours = request.POST.get('duration_in_hours')
        normal_price = request.POST.get('normal_price')
        discount_price = request.POST.get('discount_price')

        if not all([name, duration_months, duration_hours, normal_price]):
            messages.error(request, 'All fields are required')
            return redirect('manage_subscriptions', library_id=subscription.library.id)

        subscription.name = name
        subscription.duration_in_months = int(duration_months)
        subscription.duration_in_hours = int(duration_hours)
        subscription.normal_price = Decimal(normal_price)
        subscription.discount_price = Decimal(discount_price) if discount_price else None
        
        subscription.save()
        messages.success(request, 'Subscription updated successfully')
        
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, 'Subscription not found')
    except ValueError as e:
        messages.error(request, f'Invalid input: {str(e)}')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('manage_subscriptions', library_id=subscription.library.id)

@require_POST
@login_required
def toggle_coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    coupon.is_active = not coupon.is_active
    coupon.save()
    
    return redirect('manage_coupons', library_id=coupon.library.id)

@csrf_exempt
@require_POST
def handle_payment_success(request):
    try:
        data = json.loads(request.body)
        coupon_id = data.get('coupon_id')
        
        if not coupon_id:
            logger.error("No coupon ID provided in payment success")
            return JsonResponse({
                'success': False,
                'message': 'Coupon ID is required'
            }, status=400)

        coupon = Coupon.objects.get(id=coupon_id)
        
        # Only increment usage if payment was successful
        if coupon.times_used < coupon.max_usage:
            coupon.times_used += 1
            coupon.save()
            logger.info(f"Successfully updated coupon {coupon_id} usage count")
        else:
            logger.warning(f"Coupon {coupon_id} has reached max usage")

        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully'
        })

    except Coupon.DoesNotExist:
        logger.error(f"Coupon {coupon_id} not found")
        return JsonResponse({
            'success': False,
            'message': 'Invalid coupon ID'
        }, status=404)
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while processing payment: {str(e)}'
        }, status=500)
    

@login_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    library = coupon.library
    
    # Check if the user has permission to edit this coupon
    if request.user != coupon.created_by:
        raise PermissionDenied("You don't have permission to edit this coupon")

    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon, library_id=library.id)
        if form.is_valid():
            coupon = form.save(commit=False)
            
            # Handle "All Plans" selection
            if 'all' in form.cleaned_data['applicable_plans']:
                coupon.applicable_plans.set(SubscriptionPlan.objects.filter(library=library))
            else:
                coupon.save()
                form.save_m2m()
            
            messages.success(request, "Coupon updated successfully!")
            return redirect('manage_coupons', library_id=library.id)
    else:
        form = CouponForm(instance=coupon, library_id=library.id)
    
    return render(request, 'library/edit_coupon.html', {
        'library': library,
        'form': form,
        'coupon': coupon
    })

@login_required
@require_POST
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    # Check if the user has permission to delete this coupon
    if request.user != coupon.created_by:
        raise PermissionDenied("You don't have permission to delete this coupon")
    
    coupon.delete()
    messages.success(request, "Coupon deleted successfully!")
    return redirect('manage_coupons', library_id=coupon.library.id)

@login_required
@require_POST
def appoint_staff(request, library_id, user_id):
    if request.method == 'POST':
        try:
            library = Library.objects.get(id=library_id)
            user = User.objects.get(id=user_id)
            
            if user in library.staff.all():
                return JsonResponse({'success': False, 'message': 'User is already a staff member'})
            
            library.staff.add(user)
            return JsonResponse({'success': True, 'message': 'User appointed successfully'})
        
        except Library.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Library not found'}, status=404)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
def update_upi_data(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to update UPI data for this library")
    
    if request.method == 'POST':
        library.upi_id = request.POST.get('upi_id')
        library.recipient_name = request.POST.get('recipient_name')
        library.thank_you_message = request.POST.get('thank_you_message')
        library.save()
        messages.success(request, 'UPI data updated successfully!')
        return redirect('library_dashboard', library_id=library.id)
    
    return redirect('library_dashboard', library_id=library.id)

@login_required
@require_POST
def remove_staff(request, library_id, user_id):
    library = get_object_or_404(Library, id=library_id)
    user = get_object_or_404(User, id=user_id)
    
    # Check if the current user is the library owner
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to remove staff from this library")
    
    # Remove the user from staff
    library.staff.remove(user)
    messages.success(request, f'{user.get_full_name()} has been removed from staff')
    
    return redirect('library_dashboard', library_id=library.id)

@login_required
def staff_dashboard(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.user not in library.staff.all():
        raise PermissionDenied("You don't have permission to access this dashboard")
    
    # Get staff permissions from VendorSSID table
    staff_permissions = []
    try:
        vendor_ssid = VendorSSID.objects.filter(
            user=request.user,
            library=library
        ).first()
        
        if vendor_ssid:
            staff_permissions = vendor_ssid.permissions.split(',') if vendor_ssid.permissions else []
    except Exception as e:
        logger.error(f"Error getting staff permissions: {str(e)}")
    
    # Get today's date
    today = timezone.now().date()
    
    # Get dashboard stats
    active_users_count = UserSubscription.objects.filter(
        subscription__library=library,
        end_date__gte=today
    ).values('user').distinct().count()
    
    # Filter attendance by check_in_time instead of date
    todays_attendance_count = LibraryAttendance.objects.filter(
        library=library,
        check_in_time__date=today
    ).count()
    
    active_subscriptions_count = UserSubscription.objects.filter(
        subscription__library=library,
        end_date__gte=today
    ).count()
    
    return render(request, 'library/staff_dashboard.html', {
        'library': library,
        'active_users_count': active_users_count,
        'todays_attendance_count': todays_attendance_count,
        'active_subscriptions_count': active_subscriptions_count,
        'staff_permissions': staff_permissions
    })

@login_required
def manage_banner(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    # Check if user has permission to manage banners
    if request.user != library.owner and request.user not in library.staff.all():
        raise PermissionDenied("You don't have permission to manage banners for this library")
    
    banners = library.banners.order_by('-created_at')
    
    if request.method == 'POST':
        form = BannerForm(request.POST)
        if form.is_valid():
            # Check max banner limit
            if banners.count() >= library.max_banners:
                messages.error(request, f'You can only have {library.max_banners} banners')
                return redirect('manage_banner', library_id=library.id)
                
            banner = form.save(commit=False)
            banner.library = library
            banner.save()
            messages.success(request, 'Banner added successfully!')
            return redirect('manage_banner', library_id=library.id)
        else:
            messages.error(request, 'Invalid banner data. Please check the form.')
    else:
        form = BannerForm()
    
    context = {
        'library': library,
        'banners': banners,
        'form': form,
    }
    
    return render(request, 'library/manage_banner.html', context)
    
@login_required
def delete_banner(request, banner_id):
    banner = get_object_or_404(Banner, id=banner_id)
    library_id = banner.library.id
    banner.delete()
    messages.success(request, 'Banner deleted successfully!')
    return redirect('manage_banner', library_id=library_id)

@login_required
def update_library_image(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    if request.method == 'POST':
        form = LibraryImageForm(request.POST)
        if form.is_valid():
            # Get or create the LibraryImage instance
            image, created = LibraryImage.objects.get_or_create(library=library)
            # Update the fields
            image.google_drive_link = form.cleaned_data['google_drive_link']
            image.save()
            messages.success(request, 'Library image updated successfully!')
        else:
            # If form is invalid, show error messages
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('library_dashboard', library_id=library_id)

def remove_library_image(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    try:
        library.image.delete()
        return JsonResponse({'status': 'success', 'message': 'Image removed successfully'})
    except LibraryImage.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No image to remove'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def update_banner(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        text = request.POST.get('banner_text', '').strip()
        if text:
            # Get or create banner
            banner = HomePageTextBanner.objects.first()
            if not banner:
                banner = HomePageTextBanner()
            banner.text = text
            banner.is_active = True
            banner.save()
            messages.success(request, 'Banner updated successfully!')
        else:
            messages.error(request, 'Banner text cannot be empty')
    
    return redirect('admin_dashboard')

@login_required
def manage_home_banners(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    banners_image = HomePageImageBanner.objects.all()
    
    if request.method == 'POST':
        form = HomePageBannerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner added successfully!')
            return redirect('manage_home_banners')
    else:
        form = HomePageBannerForm()
    
    return render(request, 'admin_page/manage_home_banners.html', {
        'banners': banners_image,
        'form': form
    })

@login_required
def delete_home_banner(request, banner_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    banner_image = get_object_or_404(HomePageImageBanner, id=banner_id)
    banner_image.delete()
    messages.success(request, 'Banner deleted successfully!')
    return redirect('manage_home_banners')

@login_required
def manage_text_banner(request):
    if request.method == 'POST':
        text = request.POST.get('banner_text', '').strip()
        is_active = request.POST.get('is_active', False) == 'on'
        
        if text:  # Only create if there's text
            banner = HomePageTextBanner(text=text, is_active=is_active)
            banner.save()
            messages.success(request, 'Text banner added successfully!')
        else:
            messages.error(request, 'Banner text cannot be empty')
    
    banners = HomePageTextBanner.objects.all()
    return render(request, 'admin_page/manage_text_banner.html', {
        'banners': banners
    })

@login_required
def delete_text_banner(request, banner_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    banner = get_object_or_404(HomePageTextBanner, id=banner_id)
    banner.delete()
    messages.success(request, 'Banner deleted successfully!')
    return redirect('manage_text_banner')

@login_required
def manage_banner_counts(request):
    if not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == 'POST':
        library_id = request.POST.get('library_id')
        institution_id = request.POST.get('institution_id')
        gym_id = request.POST.get('gym_id')
        max_banners = request.POST.get('max_banners')
        msg = ''
        if library_id:
            library = get_object_or_404(Library, id=library_id)
            library.max_banners = max_banners
            library.save()
            msg = 'Library banner count updated successfully!'
        elif institution_id:
            institution = get_object_or_404(Institution, id=institution_id)
            institution.max_banners = max_banners
            institution.save()
            msg = 'Institution banner count updated successfully!'
        elif gym_id:
            gym = get_object_or_404(Gym, id=gym_id)
            gym.max_banners = max_banners
            gym.save()
            msg = 'Gym banner count updated successfully!'
        else:
            msg = 'No valid entity provided for banner update.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg})
            messages.error(request, msg)
            return redirect('manage_banner_counts')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        messages.success(request, msg)
        return redirect('manage_banner_counts')
    
    search_query = request.GET.get('search', '')
    libraries = Library.objects.all()
    institutions = Institution.objects.all()
    gyms = Gym.objects.all()
    
    if search_query:
        libraries = libraries.filter(
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(venue_name__icontains=search_query)
        )
        institutions = institutions.filter(
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(name__icontains=search_query)
        )
        gyms = gyms.filter(
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    return render(request, 'admin_page/manage_banner_counts.html', {
        'libraries': libraries,
        'institutions': institutions,
        'gyms': gyms,
        'search_query': search_query
    })

@login_required
def add_review(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    # Check if user has already reviewed
    existing_review = Review.objects.filter(library=library, user=request.user).first()
    if existing_review:
        messages.info(request, "Your review means a lot to us! Thank you for your feedback.")
        return redirect('library_details', library_id=library_id)
    
    # Check if user has active subscription
    has_active_subscription = UserSubscription.objects.filter(
        user=request.user,
        subscription__library=library,
        end_date__gte=timezone.now().date()
    ).exists()
    
    if not has_active_subscription:
        messages.error(request, "You need an active subscription to review this library.")
        return redirect('library_details', library_id=library_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.library = library
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully!")
            return redirect('library_details', library_id=library_id)
    else:
        form = ReviewForm()
    
    return render(request, 'library/add_review.html', {
        'form': form,
        'library': library,
        'has_reviewed': existing_review is not None
    })

@login_required
def manage_reviews(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    
    # Check if user is owner or staff
    if request.user != library.owner and request.user not in library.staff.all():
        raise PermissionDenied("You don't have permission to manage reviews")
    
    reviews = library.get_reviews()
    
    # Pagination
    paginator = Paginator(reviews, 25)  # Show 10 reviews per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/manage_reviews.html', {
        'library': library,
        'page_obj': page_obj
    })

@login_required
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    library = review.library
    
    # Check if user is owner or staff
    if request.user != library.owner and request.user not in library.staff.all():
        raise PermissionDenied("You don't have permission to delete this review")
    
    review.delete()
    messages.success(request, "Review deleted successfully!")
    return redirect('manage_reviews', library_id=library.id)

@login_required
def view_reviews(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    reviews = library.reviews.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/view_reviews.html', {
        'library': library,
        'page_obj': page_obj
    })

def apply_vendor(request):
    return render(request, 'library/apply_vendor.html')

def about_us(request):
    return render(request, 'users_pages/about_us.html')

@require_POST
@login_required
def add_permission(request, library_id, staff_id):
    library = get_object_or_404(Library, id=library_id)
    staff_member = get_object_or_404(CustomUser, id=staff_id)
    
    if request.user != library.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    permission = data.get('permission')
    
    if not permission:
        return JsonResponse({'success': False, 'message': 'Permission is required'}, status=400)
    
    try:
        vendor_ssid = staff_member.vendor_ssids.filter(library=library).first()
        if vendor_ssid:
            permissions = vendor_ssid.permissions.split(',') if vendor_ssid.permissions else []
            if permission not in permissions:
                permissions.append(permission)
                vendor_ssid.permissions = ','.join(permissions)
                vendor_ssid.save()
                return JsonResponse({'success': True, 'message': 'Permission added successfully'})
            return JsonResponse({'success': False, 'message': 'Permission already exists'})
        return JsonResponse({'success': False, 'message': 'Staff member not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding permission: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)

@login_required
@require_POST
def remove_permission(request, library_id, staff_id):
    library = get_object_or_404(Library, id=library_id)
    staff_member = get_object_or_404(CustomUser, id=staff_id)
    
    if request.user != library.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    permission = data.get('permission')
    
    if not permission:
        return JsonResponse({'success': False, 'message': 'Permission is required'}, status=400)
    
    try:
        # Check if staff member is part of this library
        if staff_member not in library.staff.all():
            return JsonResponse({'success': False, 'message': 'Staff member not found in this library'}, status=404)
        
        # Get the vendor_ssids relationship
        vendor_ssid = VendorSSID.objects.filter(
            user=staff_member,
            library=library
        ).first()
        
        if vendor_ssid and vendor_ssid.permissions:
            # Remove the permission if it exists
            permissions = vendor_ssid.permissions.split(',')
            if permission in permissions:
                permissions.remove(permission)
                vendor_ssid.permissions = ','.join(permissions)
                vendor_ssid.save()
                return JsonResponse({'success': True, 'message': 'Permission removed successfully'})
            return JsonResponse({'success': False, 'message': 'Permission not found'}, status=404)
        return JsonResponse({'success': False, 'message': 'No permissions found for this staff member'}, status=404)
    except Exception as e:
        logger.error(f"Error removing permission: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)

@login_required
@require_POST
def manage_permissions(request, library_id, staff_id):
    library = get_object_or_404(Library, id=library_id)
    staff_member = get_object_or_404(CustomUser, id=staff_id)
    
    if request.user != library.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    permissions = list(set(data.get('permissions', [])))  # Remove duplicates
    
    try:
        # Ensure the staff member is part of the library's staff
        if staff_member not in library.staff.all():
            return JsonResponse({'success': False, 'message': 'Staff member not found in this library'}, status=404)
        
        # Get existing vendor_ssids relationship
        vendor_ssid = VendorSSID.objects.filter(
            user=staff_member,
            library=library
        ).first()
        
        if vendor_ssid:
            # Update existing permissions
            vendor_ssid.permissions = ','.join(permissions)
            vendor_ssid.save()
        else:
            # Create new vendor_ssids relationship only if there are permissions to add
            if permissions:
                VendorSSID.objects.create(
                    user=staff_member,
                    library=library,
                    permissions=','.join(permissions)
                )
            else:
                return JsonResponse({'success': False, 'message': 'No permissions to add'}, status=400)
        
        return JsonResponse({'success': True, 'message': 'Permissions updated successfully'})
    except Exception as e:
        logger.error(f"Error managing permissions: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)

@login_required
def get_permissions(request, library_id, staff_id):
    library = get_object_or_404(Library, id=library_id)
    staff_member = get_object_or_404(CustomUser, id=staff_id)
    
    # Check if user is owner or staff
    if request.user != library.owner and request.user not in library.staff.all():
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        # Check if staff member is actually part of this library
        if staff_member not in library.staff.all():
            return JsonResponse({'success': False, 'message': 'Staff member not found in this library'}, status=404)
        
        # Get the vendor_ssids relationship
        vendor_ssid = VendorSSID.objects.filter(
            user=staff_member,
            library=library
        ).first()
        
        # Return permissions, even if empty
        permissions = vendor_ssid.permissions.split(',') if vendor_ssid and vendor_ssid.permissions else []
        return JsonResponse({'success': True, 'permissions': permissions})
        
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)

@login_required
def library_user_details(request, library_id, user_id):
    library = get_object_or_404(Library, id=library_id)
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if user has permission to view this user's details
    if not request.user.has_perm('library.view_user_details'):
        return redirect('home')
    
    return render(request, 'library/user_details.html', {
        'user': user,
        'library': library
    })

@csrf_exempt
def mark_attendance_manual(request, user_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            library_id = data.get('library_id')
            
            if not library_id:
                return JsonResponse({"error": "Library ID is required"}, status=400)
            
            user = CustomUser.objects.get(id=user_id)
            library = Library.objects.get(id=library_id)
            
            current_time = timezone.now()
            latest_attendance = LibraryAttendance.objects.filter(
                user=user,
                library=library
            ).order_by('-check_in_time').first()
            
            if not latest_attendance or latest_attendance.check_out_time:
                # Check if seats are available
                if library.available_seats <= 0:
                    return JsonResponse({
                        "error": "No seats available",
                        "status": "full"
                    }, status=400)
                
                # New check-in
                LibraryAttendance.objects.create(
                    user=user,
                    library=library,
                    check_in_time=current_time,
                    check_in_color=0,
                    check_out_color=0,
                    nfc_id=user.nfc_id
                )
                
                # Decrease available seats
                library.available_seats -= 1
                library.save()
                
                return JsonResponse({
                    "success": True,
                    "message": "Checked in successfully",
                    "action": "checkin",
                    "available_seats": library.available_seats
                })
            else:
                # Check-out
                latest_attendance.check_out_time = current_time
                latest_attendance.save()
                
                # Increase available seats
                library.available_seats += 1
                library.save()
                
                return JsonResponse({
                    "success": True,
                    "message": "Checked out successfully",
                    "action": "checkout",
                    "available_seats": library.available_seats
                })
                
        except CustomUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found"}, status=404)
        except Library.DoesNotExist:
            return JsonResponse({"success": False, "error": "Library not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

@login_required
def manage_cards(request):
    # Only get cards that are allocated to a library
    cards = AdminCard.objects.filter(library__isnull=False).select_related('library')
    
    search_query = request.GET.get('search')
    if search_query:
        cards = cards.filter(
            Q(card_id__icontains=search_query) |
            Q(library__venue_name__icontains=search_query)
        )
    
    paginator = Paginator(cards, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_page/manage_cards.html', {
        'cards': page_obj
    })

def add_card(request):
    if request.method == 'POST':
        try:
            # Handle modern AJAX requests with JSON body
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                card_id = data.get('card_id')
            else:
                # Fallback for traditional form submissions
                card_id = request.POST.get('card_id')

            if not card_id:
                return JsonResponse({'status': 'error', 'message': 'NFC Card ID is required.'}, status=400)

            if AdminCard.objects.filter(card_id=card_id).exists():
                return JsonResponse({'status': 'error', 'message': f'Card with ID {card_id} already exists.'}, status=400)

            AdminCard.objects.create(card_id=card_id)
            return JsonResponse({'status': 'success', 'message': f'Card {card_id} added successfully!'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON in request body.'}, status=400)
        except Exception as e:
            logger.error(f"Error in add_card view: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': 'An unexpected server error occurred.'}, status=500)
            
    # For GET requests
    return render(request, 'admin_page/add_card.html')

def allocate_card(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            user_id = data.get("user_id")
            
            # Check if card exists in admin-approved list
            if not AdminCard.objects.filter(card_id=nfc_serial).exists():
                return JsonResponse({'error': 'This card is not approved for use'}, status=400)

            # Rest of the allocation logic...
            return JsonResponse({'success': True, 'message': 'Card allocated successfully'})
            
        except Exception as e:
            logger.error(f"Error in allocate function: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_card(request, card_id):
    try:
        card = AdminCard.objects.get(id=card_id)
        card.delete()
        return redirect('manage_cards')
    except AdminCard.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)

@login_required
@csrf_exempt
def check_card_in_admin_db(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_serial = data.get('nfc_serial')
            
            if not nfc_serial:
                return JsonResponse({'error': 'NFC serial is required'}, status=400)
            
            exists = AdminCard.objects.filter(card_id=nfc_serial).exists()
            return JsonResponse({'exists': exists})
            
        except Exception as e:
            logger.error(f"Error in check_card_in_admin_db: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def allocate_card_to_library(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            library_id = data.get('library_id')
            nfc_serials = data.get('nfc_serials')
            
            if not library_id or not nfc_serials:
                return JsonResponse({'error': 'Library ID and at least one NFC serial are required'}, status=400)
            
            library = Library.objects.get(id=library_id)
            allocated_cards = []
            errors = []
            
            for nfc_serial in nfc_serials:
                try:
                    card = AdminCard.objects.get(card_id=nfc_serial)
                    if card.library:
                        errors.append(f'Card {nfc_serial} is already allocated to a library')
                        continue
                    
                    card.library = library
                    card.save()
                    allocated_cards.append(nfc_serial)
                except AdminCard.DoesNotExist:
                    errors.append(f'Card {nfc_serial} not found')
                    continue
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'message': 'Some cards could not be allocated',
                    'errors': errors,
                    'allocated_cards': allocated_cards
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'{len(allocated_cards)} cards allocated successfully',
                'data': {
                    'library_id': library.id,
                    'library_name': library.venue_name,
                    'allocated_cards': allocated_cards
                }
            })
            
        except Library.DoesNotExist:
            return JsonResponse({'error': 'Library not found'}, status=404)
        except Exception as e:
            logger.error(f"Error in allocate_card_to_library: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def allocate_card_to_library_page(request):
    libraries = Library.objects.all()
    # Correctly filter for cards that are not allocated to EITHER a library or an institution.
    admin_cards = AdminCard.objects.filter(library__isnull=True, institution__isnull=True, gym__isnull=True)
    return render(request, 'admin_page/allocate_card_to_library.html', {
        'libraries': libraries,
        'admin_cards': admin_cards
    })

@login_required
def deallocate_card(request, card_id):
    if request.method == 'POST':
        try:
            card = AdminCard.objects.get(id=card_id)
            card.library = None
            card.save()
            messages.success(request, 'Card deallocated successfully')
        except AdminCard.DoesNotExist:
            messages.error(request, 'Card not found')
        return redirect('manage_cards')
    
@login_required
def allocate_card_count(request):
    libraries = Library.objects.annotate(
        allocated_cards_count=Count('admin_cards', distinct=True)
    ).order_by('venue_name')
    
    library_data = [{
        'venue_name': library.venue_name,
        'allocated_cards_count': library.allocated_cards_count,
        'owner': library.owner
    } for library in libraries]
    
    return render(request, 'admin_page/allocate_card_count.html', {
        'libraries': library_data
    })

@login_required
def admin_graphs(request):
    if not request.user.is_staff:
        raise PermissionDenied
    
    # Data for charts
    libraries = Library.objects.annotate(
        allocated_cards_count=Count('admin_cards')
    ).order_by('-allocated_cards_count')[:10]  # Top 10 libraries

    institutions = Institution.objects.annotate(
        allocated_cards_count=Count('admin_cards')
    ).order_by('-allocated_cards_count')[:10] # Top 10 institutions
    
    user_counts = {
        'total': CustomUser.objects.count(),
        'active': CustomUser.objects.filter(is_active=True).count(),
        'inactive': CustomUser.objects.filter(is_active=False).count()
    }
    
    subscription_data = {
        'active': UserSubscription.objects.filter(end_date__gte=timezone.now().date()).count(),
        'expired': UserSubscription.objects.filter(end_date__lt=timezone.now().date()).count()
    }
    
    return render(request, 'admin_page/admin_graphs.html', {
        'libraries': libraries,
        'institutions': institutions,
        'user_counts': user_counts,
        'subscription_data': subscription_data
    })

@login_required
def Manage_Admin_loss(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('expense_name')
            amount = request.POST.get('amount')
            date = request.POST.get('date')
            description = request.POST.get('description')
            
            # Basic validation
            if not all([name, amount, date]):
                messages.error(request, 'All fields are required')
                return redirect('Manage_Admin_Expenss')
            
            # Create new expense with type set to Loss
            AdminExpense.objects.create(
                name=name,
                amount=amount,
                date=date,
                description=description,
                type='Loss',  # Set type to Loss
                created_by=request.user
            )
            messages.success(request, 'Expense added successfully')
            return redirect('Manage_Admin_Expenss')
            
        except Exception as e:
            logger.error(f"Error adding expense: {str(e)}")
            messages.error(request, 'An error occurred while adding the expense')
            return redirect('Manage_Admin_Expenss')

    # Get all expenses for display, filtering for Loss type
    expenses = AdminExpense.objects.filter(type='Loss').order_by('-date')
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_title': 'Manage Admin Expenses',
        'expenses': expenses,
        'total_expenses': total_expenses,
        'today': now().date()  # Add today's date to context
    }
    return render(request, 'admin_page/manage_admin_loss.html', context)

@login_required
def EditAdminExpense_loss(request, expense_id):
    expense = get_object_or_404(AdminExpense, id=expense_id, type='Loss')  # Ensure we're only editing Loss type expenses
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('expense_name')
            amount = request.POST.get('amount')
            date = request.POST.get('date')
            description = request.POST.get('description')
            
            # Basic validation
            if not all([name, amount, date]):
                return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)
            
            # Update expense
            expense.name = name
            expense.amount = amount
            expense.date = date
            expense.description = description
            expense.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error updating expense: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def DeleteAdminExpense_loss(request, expense_id):
    expense = get_object_or_404(AdminExpense, id=expense_id, type='Loss')  # Ensure we're only deleting Loss type expenses
    if request.method == 'POST':
        try:
            expense.delete()
            messages.success(request, 'Expense deleted successfully')
            return redirect('Manage_Admin_Expenss')
        except Exception as e:
            logger.error(f"Error deleting expense: {str(e)}")
            messages.error(request, 'An error occurred while deleting the expense')
            return redirect('Manage_Admin_Expenss')
    else:
        messages.error(request, 'Invalid request method')
        return redirect('Manage_Admin_Expenss')
    

@login_required
def Manage_Admin_profit(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('expense_name')
            amount = request.POST.get('amount')
            date = request.POST.get('date')
            description = request.POST.get('description')
            
            # Basic validation
            if not all([name, amount, date]):
                messages.error(request, 'All fields are required')
                return redirect('Manage_Admin_Profit')
            
            # Create new expense with type set to Profit
            AdminExpense.objects.create(
                name=name,
                amount=amount,
                date=date,
                description=description,
                type='Profit',  # Set type to Profit
                created_by=request.user
            )
            messages.success(request, 'Profit added successfully')
            return redirect('Manage_Admin_Profit')
            
        except Exception as e:
            logger.error(f"Error adding profit: {str(e)}")
            messages.error(request, 'An error occurred while adding the profit')
            return redirect('Manage_Admin_Profit')

    # Get all profits for display, filtering for Profit type
    profits = AdminExpense.objects.filter(type='Profit').order_by('-date')
    total_profits = profits.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_title': 'Manage Admin Profits',
        'profits': profits,
        'total_profits': total_profits,
        'today': now().date()
    }
    return render(request, 'admin_page/manage_admin_profit.html', context)


@login_required
def balance_sheet(request):
    # Get all profits and losses
    profits = AdminExpense.objects.filter(type='Profit').order_by('-date')
    losses = AdminExpense.objects.filter(type='Loss').order_by('-date')
    Expenses = AdminExpense.objects.all().order_by('-date')
    
    # Calculate totals
    total_profits = profits.aggregate(total=Sum('amount'))['total'] or 0
    total_losses = losses.aggregate(total=Sum('amount'))['total'] or 0
    net_balance = total_profits - total_losses
    
    context = {
        'page_title': 'Balance Sheet',
        'Expenses': Expenses,
        'total_profits': total_profits,
        'total_losses': total_losses,
        'net_balance': net_balance,
        'today': now().date()
    }
    return render(request, 'admin_page/balance_sheet.html', context)

@login_required
def allocate_card_to_institution_page(request):
    if not request.user.is_staff:
        return redirect('home')
    
    institutions = Institution.objects.all()
    # Correctly filter for cards that are not allocated to EITHER a library or an institution.
    admin_cards = AdminCard.objects.filter(library__isnull=True, institution__isnull=True, gym__isnull=True)
    return render(request, 'admin_page/allocate_card_to_institution.html', {
        'institutions': institutions,
        'admin_cards': admin_cards
    })

@login_required
@csrf_exempt
def allocate_card_to_institution(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            institution_id = data.get('institution_id')
            nfc_serials = data.get('nfc_serials')
            
            if not institution_id or not nfc_serials:
                return JsonResponse({'error': 'Institution ID and at least one NFC serial are required'}, status=400)
            
            institution = Institution.objects.get(id=institution_id)
            allocated_cards = []
            errors = []
            
            for nfc_serial in nfc_serials:
                try:
                    card = AdminCard.objects.get(card_id=nfc_serial)
                    if card.library or card.institution:
                        errors.append(f'Card {nfc_serial} is already allocated')
                        continue
                    
                    card.institution = institution
                    card.save()
                    allocated_cards.append(nfc_serial)
                except AdminCard.DoesNotExist:
                    errors.append(f'Card {nfc_serial} not found')
                    continue
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'message': 'Some cards could not be allocated',
                    'errors': errors,
                    'allocated_cards': allocated_cards
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'{len(allocated_cards)} cards allocated successfully',
                'data': {
                    'institution_id': institution.id,
                    'institution_name': institution.name,
                    'allocated_cards': allocated_cards
                }
            })
            
        except Institution.DoesNotExist:
            return JsonResponse({'error': 'Institution not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def institution_card_count(request):
    if not request.user.is_staff:
        return redirect('home')
    
    institutions = Institution.objects.annotate(
        allocated_cards_count=Count('admin_cards', distinct=True)
    ).order_by('name')
    
    institution_data = [{
        'name': institution.name,
        'allocated_cards_count': institution.allocated_cards_count,
        'owner': institution.owner
    } for institution in institutions]
    
    return render(request, 'admin_page/institution_card_count.html', {
        'institutions': institution_data
    })

@login_required
def create_edit_schedule(request,  institution_uid):

    institution = get_object_or_404(Institution, uid=institution_uid)
    subject_faculty_qs = SubjectFacultyMap.objects.filter(institution=institution)
    classroom_names = [c['name'] for c in institution.classrooms.values()]
    subject_names = list(subject_faculty_qs.values_list('subject', flat=True))
    subject_faculty_list = list(subject_faculty_qs.values('subject', 'faculty_ssid', 'faculty_name'))
    timetable_entries = list(TimetableEntry.objects.filter(institution=institution).values())
    
    # Build a mapping: (day, classroom, cell_col) -> entry
    timetable_map = {}
    for entry in timetable_entries:
        key = (entry['day'], entry['classroom'], entry['cell_col'])
        timetable_map[key] = entry
    
    # Build a mapping: (day, cell_col) -> entry for header times
    header_time_map = {}
    for entry in timetable_entries:
        key = (entry['day'], entry['cell_col'])
        if key not in header_time_map:
            header_time_map[key] = entry
    
    # Find max col for each day
    from collections import defaultdict
    max_cols = defaultdict(int)
    for entry in timetable_entries:
        day = entry['day']
        col = entry.get('cell_col', 0)
        if col + 1 > max_cols[day]:
            max_cols[day] = col + 1  # +1 because col is zero-based
    day_col_indices = {day: list(range(max_col)) for day, max_col in max_cols.items()}
    
    # Determine unique classrooms for each day from timetable_entries
    scheduled_classrooms = defaultdict(set)
    for entry in timetable_entries:
        if entry['classroom']:
            scheduled_classrooms[entry['day']].add(entry['classroom'])
    day_row_indices = {day: sorted(list(classrooms)) for day, classrooms in scheduled_classrooms.items()}
    
    return render(request, 'coaching/create_edit_schedule.html', {
        'institution': institution,
        'timetable_map': timetable_map,
        'header_time_map': header_time_map,
        'day_col_indices': day_col_indices,
        'day_row_indices': day_row_indices,
        'classroom_names': classroom_names,
        'subject_names': subject_names,
        'subject_faculty_list': subject_faculty_list,
    })

@login_required
@require_POST
def allocate_card_to_user(request):
    card_id = request.POST.get('card_id')
    user_id = request.POST.get('user_id')
    library_id = request.POST.get('library_id')

    if not all([card_id, user_id, library_id]):
        return JsonResponse({'status': 'error', 'message': 'Card ID, User, and Library are required.'}, status=400)

    library = get_object_or_404(Library, id=library_id)
    user_to_allocate = get_object_or_404(CustomUser, id=user_id)

    # Check permission
    if request.user != library.owner:
        return JsonResponse({'status': 'error', 'message': "You don't have permission to perform this action."}, status=403)

    # Check if the card is available in AdminCard
    try:
        admin_card = AdminCard.objects.get(card_id=card_id)
        if admin_card.library or admin_card.institution:
            return JsonResponse({'status': 'error', 'message': 'This card is already allocated.'}, status=400)
    except AdminCard.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'This card is not registered in the system.'}, status=400)

    # Final check for an active subscription
    has_active_subscription = UserSubscription.objects.filter(
        user=user_to_allocate,
        subscription__library=library,
        status='valid'
    ).exists()

    if not has_active_subscription:
        return JsonResponse({'status': 'error', 'message': f"User {user_to_allocate.get_full_name()} does not have a valid subscription for this library."}, status=400)

    # Allocate card
    try:
        with transaction.atomic():
            # Assign card to library in AdminCard
            admin_card.library = library
            admin_card.save()

            # Log the allocation in LibraryCardLog
            LibraryCardLog.objects.create(
                library=library,
                user=user_to_allocate,
                card_id=card_id,
                allocated_by=request.user
            )

        return JsonResponse({'status': 'success', 'message': f"Card {card_id} allocated to {user_to_allocate.get_full_name()} successfully."})
    except Exception as e:
        logger.error(f"Error in allocate_card_to_user: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred during allocation.'}, status=500)


@login_required
def unlogged_card_allocations_library(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.user != library.owner:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('vendor_dashboard', library_id=library.id)

    # Get all users who have a subscription with the library and an NFC card assigned
    subscribed_users_with_cards = CustomUser.objects.filter(
        usersubscription__subscription__library=library,
        nfc_id__isnull=False
    ).distinct()

    # Get all card IDs that are properly logged for this library
    logged_card_ids = LibraryCardLog.objects.filter(
        library=library
    ).values_list('card_id', flat=True)

    # Find users whose assigned nfc_id is NOT in the log table
    users_with_unlogged_cards = []
    for user in subscribed_users_with_cards:
        if user.nfc_id not in logged_card_ids:
            users_with_unlogged_cards.append(user)

    context = {
        'library': library,
        'users_with_unlogged_cards': users_with_unlogged_cards
    }
    return render(request, 'library/unlogged_card_allocations.html', context)

@login_required
@csrf_exempt
def allocate_institution_card(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            user_id = data.get("user_id")
            institution_id = data.get("institution_id")

            if not all([nfc_serial, user_id, institution_id]):
                return JsonResponse({'error': 'NFC serial, user ID, and institution ID are required'}, status=400)

            institution = get_object_or_404(Institution, id=institution_id)
            user = get_object_or_404(CustomUser, id=user_id)

            # Check if card is registered and allocated to THIS institution
            try:
                admin_card = AdminCard.objects.get(card_id=nfc_serial, institution=institution)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'This card is not allocated to this institution.'}, status=400)

            # Check if the user already has a card allocated in this institution
            if InstitutionCardLog.objects.filter(user=user, institution=institution).exists():
                return JsonResponse({'error': 'This user already has a card allocated in this institution.'}, status=400)
            
            # Check if the specific card is already assigned to another user in this institution
            if InstitutionCardLog.objects.filter(card_id=nfc_serial, institution=institution).exists():
                return JsonResponse({'error': 'This card is already assigned to another user.'}, status=400)

            # Log the allocation
            InstitutionCardLog.objects.create(
                institution=institution,
                user=user,
                card_id=nfc_serial,
                allocated_by=request.user
            )
            return JsonResponse({
                'success': True,
                'message': 'User activated successfully',
                'user': {
                    'id': user.id,
                    'name': user.get_full_name(),
                    'mobile': user.mobile_number
                }
            })
        except Exception as e:
            logger.error(f"Error in allocate_institution_card: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
@login_required
@csrf_exempt
def deallocate_institution_nfc(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            if not nfc_serial:
                return JsonResponse({'error': 'NFC serial is required'}, status=400)
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'No card found with this NFC ID'}, status=404)
            if card.institution is None:
                return JsonResponse({'error': 'This card is not allocated to any institution'}, status=400)

            # Delete all allocation logs for this card
            InstitutionCardLog.objects.filter(card_id=nfc_serial, institution=card.institution).delete()
            
            # Remove institution association from the card
            card.institution = None
            card.save()
            
            return JsonResponse({'success': True, 'message': 'NFC ID deallocated and all related data deleted successfully'})
        except Exception as e:
            logger.error(f"Error in deallocate_institution_nfc: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def check_institution_nfc_allocation(request):
    if request.method == 'POST':
        try:
            if request.content_type != 'application/json':
                return JsonResponse({'error': 'Invalid content type, expected application/json'}, status=400)
            data = json.loads(request.body)
            nfc_serial = data.get('nfc_serial')
            institution_id = data.get('institution_id')
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
                institution = Institution.objects.get(id=institution_id)
            except (AdminCard.DoesNotExist, Institution.DoesNotExist):
                return JsonResponse({'error': 'Card or institution not found'}, status=404)
            if card.institution and str(card.institution.id) == str(institution_id):
                log = InstitutionCardLog.objects.filter(card_id=nfc_serial, institution=institution).order_by('-timestamp').first()
                user = log.user if log else None
                response_data = {
                    'allocated': bool(user),
                    'nfcid': nfc_serial,
                    'timestamp': timezone.now().isoformat()
                }
                if user:
                    response_data.update({
                        'user_full_name': user.get_full_name(),
                        'user_mobile': user.mobile_number,
                        'user_id': user.id
                    })
                return JsonResponse(response_data)
            else:
                return JsonResponse({'error': 'This card is not allocated to this institution'}, status=400)
        except Exception as e:
            logger.error(f"Error checking institution NFC allocation: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def manage_gyms(request):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page")
    
    gyms = Gym.objects.all().select_related('owner')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'approved':
        gyms = gyms.filter(is_approved=True)
    elif status == 'pending':
        gyms = gyms.filter(is_approved=False)
    
    # Search by name or owner
    search_query = request.GET.get('search')
    if search_query:
        gyms = gyms.filter(
            Q(name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(pincode__icontains=search_query)
        )
    
    return render(request, 'admin_page/manage_gyms.html', {
        'gyms': gyms,
        'status': status,
        'search_query': search_query
    })

@login_required
@require_POST
def toggle_gym_approval(request, gym_id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': "You don't have permission to perform this action"}, status=403)
    
    gym = get_object_or_404(Gym, id=gym_id)
    gym.is_approved = not gym.is_approved
    gym.save()
    
    return JsonResponse({'status': 'success', 'is_approved': gym.is_approved})

@login_required
def admin_gym_details(request, gym_id):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page")
    
    gym = get_object_or_404(Gym, id=gym_id)
    return render(request, 'admin_page/admin_gym_details.html', {
        'gym': gym,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def allocate_card_to_gym_page(request):
    gyms = Gym.objects.all()
    admin_cards = AdminCard.objects.filter(library__isnull=True, institution__isnull=True, gym__isnull=True)
    return render(request, 'admin_page/allocate_card_to_gym.html', {
        'gyms': gyms,
        'admin_cards': admin_cards
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def allocate_card_to_gym(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            gym_id = data.get('gym_id')
            nfc_serials = data.get('nfc_serials', [])
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

        if not gym_id or not nfc_serials:
            return JsonResponse({'success': False, 'message': 'Missing gym ID or NFC serials.'}, status=400)

        errors = []
        allocated = []
        try:
            gym = Gym.objects.get(id=gym_id)  # Using ID as per the form
        except Gym.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Gym not found.'}, status=404)

        for serial in nfc_serials:
            try:
                card = AdminCard.objects.get(card_id=serial)
                if card.is_allocated():
                    errors.append(f'Card {serial} is already allocated.')
                    continue
                card.gym = gym
                card.save()
                allocated.append(serial)
            except AdminCard.DoesNotExist:
                errors.append(f'Card {serial} not found.')

        if errors:
            return JsonResponse({
                'success': False, 
                'message': 'Some cards could not be allocated.', 
                'errors': errors, 
                'allocated': allocated
            }, status=400)
        
        return JsonResponse({'success': True, 'message': 'Cards allocated successfully.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@user_passes_test(lambda u: u.is_superuser)
def manage_gym_cards(request):
    # Only get allocated gym cards
    allocated_cards = AdminCard.objects.filter(gym__isnull=False).select_related('gym')
    context = {
        'allocated_cards': allocated_cards,
        'total_allocated': allocated_cards.count(),
    }
    return render(request, 'gym/manage_gym_cards.html', context)

@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_gym_card(request, card_id):
    try:
        card = AdminCard.objects.get(id=card_id)
        card.delete()
        return JsonResponse({'success': True})
    except AdminCard.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def deallocate_gym_nfc(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            if not nfc_serial:
                return JsonResponse({'error': 'NFC serial is required'}, status=400)
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'No card found with this NFC ID'}, status=404)
            if card.gym is None:
                return JsonResponse({'error': 'This card is not allocated to any gym'}, status=400)
            # Remove gym association
            card.gym = None
            card.save()
            return JsonResponse({'success': True, 'message': 'NFC ID deallocated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def gym_card_count(request):
    gyms = Gym.objects.annotate(
        allocated_cards_count=Count('admin_cards', distinct=True)
    ).order_by('name')
    
    gym_data = [{
        'name': gym.name,
        'allocated_cards_count': gym.allocated_cards_count,
        'owner': gym.owner
    } for gym in gyms]
    
    return render(request, 'admin_page/gym_card_count.html', {
        'gyms': gym_data
    })