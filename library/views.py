# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin.models import LogEntry
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Local imports
from .forms import CustomUserCreationForm, LibraryRegistrationForm, ExpenseForm, UserProfileForm, CouponForm
from .models import (
    CustomUser,
    SubscriptionPlan,
    Transaction,
    Attendance,
    Library,
    Institution,
    UserSubscription,
    Expense,
    Coupon,
)

# Python standard library imports
import json
import base64
from io import BytesIO
from datetime import timedelta
import re

# Third-party imports
import qrcode
from django.views.decorators.http import require_POST
from decimal import Decimal

User = get_user_model()

def home(request):
    return render(request, 'users_pages/home.html')

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    today = timezone.now().date()
    
    # Get user's active subscriptions with their latest transaction
    active_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        end_date__gte=today
    ).select_related('subscription')
    
    # Add transaction details to each subscription
    for subscription in active_subscriptions:
        latest_transaction = Transaction.objects.filter(
            user=request.user,
            subscription=subscription.subscription
        ).order_by('-created_at').first()
        
        subscription.latest_transaction = latest_transaction
        subscription.payment_status = {
            'status': latest_transaction.status if latest_transaction else None,
            'color': 'green' if latest_transaction and latest_transaction.status == 'valid' else 
                    'yellow' if latest_transaction and latest_transaction.status == 'pending' else 
                    'red'
        }
        # Add subscription cost to each subscription
        subscription.cost = latest_transaction.amount if latest_transaction else subscription.subscription.normal_price
    
    attendances = Attendance.objects.filter(
        user=request.user
    ).order_by('-check_in_time')[:15]
    
    context = {
        'active_subscriptions': active_subscriptions,
        'attendances': attendances,
    }
    
    return render(request, 'users_pages/dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    
    total_users = CustomUser.objects.count()
    total_libraries = Library.objects.count()
    total_institutions = Institution.objects.count()
    approved_libraries = Library.objects.filter(is_approved=True).count()
    approved_institutions = Institution.objects.filter(is_approved=True).count()
    pending_libraries = total_libraries - approved_libraries
    pending_institutions = total_institutions - approved_institutions
    
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
        'pending_libraries': pending_libraries,
        'pending_institutions': pending_institutions,
        'active_subscriptions': active_subscriptions,
        'recent_activities_count': recent_activities_count
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
            user.username = form.cleaned_data['email']  # Set username as email
            user.dob = form.cleaned_data['dob']  # Ensure dob is set
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
def manage_users(request, vendor_id):
    vendor = get_object_or_404(Library, id=vendor_id)
    
    # Check if the user is the owner of this library
    if request.user != vendor.owner:
        raise PermissionDenied("You don't have permission to access this dashboard")
    
    users = CustomUser.objects.filter(
        usersubscription__subscription__user=vendor.owner
    ).distinct()

    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    return render(request, 'library/manage_users.html', {
        'users': users,
        'library': vendor
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
            
            user = CustomUser.objects.get(nfc_id=nfc_serial)
            library = Library.objects.get(id=library_id)
            
            # Check if user has active subscription
            active_subscription = UserSubscription.objects.filter(
                user=user,
                subscription__library=library,  # Access library through subscription
                end_date__gte=timezone.now().date()
            ).exists()
            
            if not active_subscription:
                return JsonResponse({"error": "User does not have an active subscription"}, status=403)
            
            latest_attendance = Attendance.objects.filter(
                user=user,
                library=library
            ).order_by('-check_in_time').first()
            
            if latest_attendance and not latest_attendance.check_out_time:
                latest_attendance.check_out_time = timezone.now()
                latest_attendance.save()
                return JsonResponse({
                    "message": f"Checked out: {user.get_full_name()}",
                    "action": "checkout",
                    "date": timezone.now().date().isoformat(),
                    "time": latest_attendance.check_out_time.strftime("%H:%M:%S")
                })
            else:
                attendance = Attendance.objects.create(
                    user=user,
                    library=library,
                    check_in_time=timezone.now(),
                    nfc_id=nfc_serial
                )
                return JsonResponse({
                    "message": f"Checked in: {user.get_full_name()}",
                    "action": "checkin",
                    "date": timezone.now().date().isoformat(),
                    "time": attendance.check_in_time.strftime("%H:%M:%S")
                })
                
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
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
            
            # Get user-provided transaction ID
            transaction_id = request.POST.get('transaction_id')
            
            # Validate transaction ID
            if not transaction_id:
                messages.error(request, "Transaction ID is required")
                return redirect('payment', plan_id=plan_id)
            
            # Check if transaction ID already exists
            if Transaction.objects.filter(transaction_id=transaction_id).exists():
                messages.error(request, "Transaction ID already exists")
                return redirect('payment', plan_id=plan_id)
            
            # Get the final price from the session
            final_price = Decimal(request.session.get('final_price', subscription_plan.normal_price))
            
            # Create transaction record with the final amount
            transaction = Transaction.objects.create(
                user=request.user,
                subscription=subscription_plan,
                transaction_id=transaction_id,
                amount=final_price,  # Use the final price after coupon
                status='pending'
            )
            
            # Create UserSubscription record
            UserSubscription.objects.create(
                user=request.user,
                subscription=subscription_plan,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=subscription_plan.duration_in_months * 30)
            )
            
            # Clear the session data
            if 'final_price' in request.session:
                del request.session['final_price']
            
            # Redirect to payment confirmation page
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
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to access this dashboard")
    
    # Get all attendance records for this library
    attendances = Attendance.objects.filter(library=library).order_by('-check_in_time')
    
    # Add search functionality
    search_query = request.GET.get('search')
    if search_query:
        attendances = attendances.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    return render(request, 'library/all_attendence.html', {
        'attendances': attendances,
        'library': library
    })

@login_required
def expense_dashboard(request, library_id):
    if not request.user.is_authenticated:
        return redirect('login')
    library = get_object_or_404(Library, id=library_id)
    
    # Check if the user is the owner
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to view this library's expenses")
    
    # Get date filters from request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Base querysets
    transactions = Transaction.objects.filter(subscription__library=library)
    expenses = Expense.objects.filter(library=library)
    
    # Apply date filters if provided
    if from_date and to_date:
        transactions = transactions.filter(created_at__range=[from_date, to_date])
        expenses = expenses.filter(date__range=[from_date, to_date])
    
    # Calculate totals
    total_earnings = transactions.aggregate(total=Sum('amount'))['total'] or 0
    valid_amount = transactions.filter(status='valid').aggregate(total=Sum('amount'))['total'] or 0
    invalid_amount = transactions.filter(status='invalid').aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_profit = float(valid_amount) - float(total_expenses)
    
    context = {
        'library': library,
        'total_earnings': total_earnings,
        'valid_amount': valid_amount,
        'invalid_amount': invalid_amount,
        'expenses': expenses.order_by('-date')[:10],
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'valid_transactions': transactions.filter(status='valid').select_related('user', 'subscription').order_by('-created_at'),
        'from_date': from_date,
        'to_date': to_date
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
    """Handle library registration"""
    if request.method == 'POST':
        form = LibraryRegistrationForm(request.POST)
        if form.is_valid():
            library = form.save(commit=False)
            library.owner = request.user
            library.business_type = 'Library'  
            library.save()
            messages.success(request, "Library registered successfully!")
            return redirect('dashboard')
    else:
        form = LibraryRegistrationForm()
    
    return render(request, 'vender/register_library.html', {'form': form})

@login_required
def register_coaching(request):
    """Handle coaching center registration"""
    if request.method == 'POST':
        form = LibraryRegistrationForm(request.POST)
        if form.is_valid():
            coaching = form.save(commit=False)
            coaching.owner = request.user
            coaching.business_type = 'Coaching'
            coaching.save()
            return redirect('register_venders_shop')
    else:
        form = LibraryRegistrationForm()
    return render(request, 'library/register_library.html', {'form': form})

def register_venders_shop(request):
    if not request.user.is_authenticated:
        return redirect('login')
    query = request.GET.get('q', '')
    libraries = Library.objects.filter(Q(venue_name__icontains=query) | Q(address__icontains=query) | Q(city__icontains=query) | Q(state__icontains=query) | Q(pincode__icontains=query))
    institutions = Institution.objects.filter()
    items = list(libraries) + list(institutions)
    
    return render(request, 'users_pages/register_venders_shop.html', {'items': items})

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
    if not request.user.is_authenticated:
        return redirect('login')
    library = get_object_or_404(Library, id=library_id)
    if not library.is_approved:
        raise Http404("Library not found")
    return render(request, 'library/library_details.html', {
        'library': library,
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
    
    # Check if the user is the owner of this library
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to access this dashboard")
    
    # Get the count of users enrolled in this library
    user_count = UserSubscription.objects.filter(
        subscription__library=library
    ).values('user').distinct().count()
    
    active_subscriptions_count = UserSubscription.objects.filter(
        subscription__library=library,
        end_date__gte=timezone.now().date()
    ).distinct().count()
    
    context = {
        'library': library,
        'user_count': user_count,
        'active_subscriptions_count': active_subscriptions_count
    }
    return render(request, 'library/library_dashboard.html', context)

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
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    coupon_code = request.GET.get('coupon')
    
    # Start with the base price (discounted or normal)
    final_price = plan.discount_price if plan.has_discount else plan.normal_price

    # Apply coupon discount if valid
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid() and plan in coupon.applicable_plans.all():
                final_price = coupon.apply_discount(final_price)
        except Coupon.DoesNotExist:
            pass

    # Store the final price in the session
    request.session['final_price'] = str(final_price)
    
    # UPI ID and payment details
    upi_id = "9625694673@ptyes"
    recipient_name = "Kanishk Kumar Singh"
    thank_you_message = "Thank you"
    
    # Create UPI payment link with final price
    upi_link = f"upi://pay?pa={upi_id}&pn={recipient_name}&mc=1234&tid=transaction123&tr=ref12345&tn={thank_you_message}&am={final_price}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    context = {
        'plan': plan,
        'library': plan.library,
        'qr_code': qr_code,
        'upi_link': upi_link,
        'final_price': final_price,
        'coupon_code': coupon_code
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
        
        subscription.latest_transaction = latest_transaction
        subscription.payment_status = {
            'status': latest_transaction.status if latest_transaction else None,
            'color': 'green' if latest_transaction and latest_transaction.status == 'valid' else 
                    'yellow' if latest_transaction and latest_transaction.status == 'pending' else 
                    'red'
        }
    
    context = {
        'subscriptions': subscriptions
    }
    return render(request, 'users_pages/user_subscriptions.html', context)

@login_required
def verify_payments(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to access this dashboard")
    
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
        # Only update allowed fields
        library.address = request.POST.get('address')
        library.description = request.POST.get('description')
        library.venue_location = request.POST.get('venue_location')
        library.venue_name = request.POST.get('venue_name')
        library.social_media_links = request.POST.get('social_media_links')
        library.business_hours = request.POST.get('business_hours')
        library.capacity = request.POST.get('capacity')
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
            user_id = data.get("user_id")  # This is the user's ID, not mobile number
            
            logger.info(f"Received allocation request - NFC: {nfc_serial}, User ID: {user_id}")

            if not nfc_serial or not user_id:
                logger.error("Missing NFC serial or user ID")
                return JsonResponse({'error': 'NFC serial and user ID are required'}, status=400)

            # Check if NFC ID is already allocated
            if CustomUser.objects.filter(nfc_id=nfc_serial).exists():
                logger.error(f"NFC ID {nfc_serial} already allocated")
                return JsonResponse({'error': 'This NFC card is already allocated to another user'}, status=400)

            try:
                # Get user by ID
                user = CustomUser.objects.get(id=user_id)
                logger.info(f"Found user: {user.id}")
                
                # Update the user's NFC ID
                user.nfc_id = nfc_serial
                user.save()
                logger.info(f"Successfully allocated NFC ID {nfc_serial} to user {user_id}")
                
                return JsonResponse({
                    'success': True, 
                    'message': 'User activated successfully',
                    'user': {
                        'id': user.id,
                        'name': user.get_full_name(),
                        'mobile': user.mobile_number
                    }
                })
                
            except CustomUser.DoesNotExist:
                logger.error(f"User not found with ID: {user_id}")
                return JsonResponse({'error': 'User not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Error in allocate function: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def nfc_add_user_page(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to access this dashboard")
    
    # Get users who have joined this library
    users = CustomUser.objects.filter(
        usersubscription__subscription__library=library
    ).distinct()
    
    context = {
        'library': library,
        'vendor': request.user,
        'users': users
    }
    return render(request, 'library/nfc_add_user.html', context)

@login_required
def attendance_page(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    # Add your attendance page logic here
    return render(request, 'library/attendance_page.html', {'library': library})

@login_required
@csrf_exempt
def check_nfc_allocation(request):
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
            
            if not nfc_serial or not isinstance(nfc_serial, str):
                return JsonResponse(
                    {'error': 'Valid NFC serial is required'}, 
                    status=400,
                    content_type='application/json'
                )
            
            # Query database
            user = CustomUser.objects.filter(nfc_id=nfc_serial).first()
            
            # Prepare response data
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

@login_required
def staff_management(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    staff_members = library.staff.all()
    return render(request, 'library/staff_management.html', {
        'library': library,
        'staff_members': staff_members
    })

@login_required
def add_staff(request, library_id):
    if request.method == 'POST':
        library = get_object_or_404(Library, id=library_id)
        
        # Ensure only the library owner can add staff
        if request.user != library.owner:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        ssid = request.POST.get('ssid')
        if not ssid:
            return JsonResponse({'success': False, 'message': 'SSID is required'}, status=400)
        
        try:
            user = CustomUser.objects.get(ssid=ssid)
            
            # Check if user is already a staff member
            if user in library.staff.all():
                return JsonResponse({'success': False, 'message': 'User is already a staff member'})
            
            # Add user to staff and update vendor relationship
            library.staff.add(user)
            
            # Store vendor's SSID in the user's vendor_ssids field
            if not user.vendor_ssids:
                user.vendor_ssids = request.user.ssid
            else:
                user.vendor_ssids += f",{request.user.ssid}"
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{user.get_full_name()} added as staff',
                'user': {
                    'full_name': user.get_full_name(),
                    'ssid': user.ssid
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
@require_POST
def search_user(request):
    if request.method == 'POST':
        ssid = request.POST.get('ssid')
        if not ssid:
            return JsonResponse({'success': False, 'message': 'SSID is required'}, status=400)
        
        try:
            user = CustomUser.objects.get(ssid=ssid)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'ssid': user.ssid
                }
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

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

            user = CustomUser.objects.filter(nfc_id=nfc_serial).first()
            if user:
                user.nfc_id = None
                user.save()
                return JsonResponse({
                    'success': True,
                    'message': 'NFC ID deallocated successfully',
                    'user': {
                        'id': user.id,
                        'name': user.get_full_name()
                    }
                })
            else:
                return JsonResponse({'error': 'No user found with this NFC ID'}, status=404)
                
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
    
    if request.user != library.owner:
        raise PermissionDenied("You don't have permission to create coupons for this library")
    
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
    
    # Check if the user has permission to modify this coupon
    if request.user != coupon.created_by:
        raise PermissionDenied("You don't have permission to modify this coupon")
    
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
            return JsonResponse({
                'success': False,
                'message': 'Coupon ID is required'
            }, status=400)

        coupon = Coupon.objects.get(id=coupon_id)
        
        # Only increment usage if payment was successful
        coupon.times_used += 1
        coupon.save()

        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully'
        })

    except Coupon.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid coupon ID'
        }, status=404)
    except Exception as e:
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