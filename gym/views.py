
from django.shortcuts import render, redirect, get_object_or_404
from .models import Gym, GymCard, GymAttendance, GymSubscriptionPlan, GymUserSubscription, GymTransaction, GymExpense, GymCoupon
from .forms import GymForm, GymRegistrationForm, GymUPIForm, GymSubscriptionPlanForm, GymUserSubscriptionForm, GymTransactionForm, GymExpenseForm, GymReviewForm, GymCouponForm
from library.models import AdminCard, CustomUser
from django.contrib import messages
from django.db import models, transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import json
import logging
from datetime import timedelta
from django.db.models.functions import TruncMonth
from collections import OrderedDict
import qrcode
from io import BytesIO
import base64
logger = logging.getLogger(__name__)

@login_required
def register_gym_form(request):
    if request.method == 'POST':
        form = GymRegistrationForm(request.POST)
        if form.is_valid():
            gym = form.save(commit=False)
            gym.owner = request.user
            gym.user = request.user
            gym.business_type = 'Gym'
            gym.save()
            messages.success(request, "Gym registered successfully!")
            return redirect('gym_registration_success')
    else:
        form = GymRegistrationForm()
    return render(request, 'gym/register_gym.html', {'form': form})

@login_required
def gym_registration_success(request):
    return render(request, 'gym/gym_registration_success.html')

def allocate_card_to_gym_page(request):
    if request.method == 'POST':
        if 'create_gym' in request.POST:
            gym_form = GymForm(request.POST)
            if gym_form.is_valid():
                gym = gym_form.save(commit=False)
                gym.owner = request.user
                gym.user = request.user
                gym.business_type = 'Gym'
                gym.description = 'Default description'
                gym.venue_location = 'Default location'
                gym.capacity = 100
                gym.pincode = '000000'
                gym.district = 'Default District'
                gym.city = 'Default City'
                gym.state = 'Default State'
                gym.opening_time = '09:00:00'
                gym.closing_time = '18:00:00'
                gym.is_approved = False
                gym.save()
                messages.success(request, 'Gym created successfully!')
                return redirect('allocate_card_to_gym_page')
        elif 'allocate_cards' in request.POST:
            gym_id = request.POST.get('gym_id') # Changed from 'gym' to 'gym_id'
            selected_cards_ids = request.POST.getlist('nfc_serials') # Changed from 'cards' to 'nfc_serials'

            try:
                gym = Gym.objects.get(id=gym_id)
                
                with transaction.atomic():
                    for card_id in selected_cards_ids: # Iterate through selected cards
                        card = AdminCard.objects.get(card_id=card_id) # Get AdminCard by card_id

                        if card.library or card.institution or card.gym: # Check if already allocated
                            messages.error(request, f'Card {card.card_id} is already allocated to a library, institution or another gym.')
                            raise Exception("Card already allocated") # Rollback transaction
                        
                        # Allocate the AdminCard to the gym
                        card.gym = gym
                        card.save()

                        messages.success(request, f'Card {card.card_id} allocated to {gym.venue_name}.')
                return redirect('allocate_card_to_gym_page')
            except Exception as e:
                messages.error(request, f'Error allocating cards: {e}')
                return redirect('allocate_card_to_gym_page')

    gym_form = GymForm()
    unallocated_cards = AdminCard.objects.filter(library__isnull=True, institution__isnull=True, gym__isnull=True)
    gyms = Gym.objects.all()
    
    context = {
        'gym_form': gym_form,
        'unallocated_cards': unallocated_cards,
        'gyms': gyms,
    }
    return render(request, 'gym/allocate_card_to_gym.html', context)

@login_required
def gym_card_count(request):
    gyms = Gym.objects.annotate(
        allocated_cards_count=Count('admin_cards', distinct=True)
    ).order_by('venue_name')

    gym_data = [{
        'venue_name': gym.venue_name,
        'allocated_cards_count': gym.allocated_cards_count,
        'total_users_with_cards': 0,  # Not implemented yet for gyms
        'owner': gym.owner
    } for gym in gyms]

    return render(request, 'gym/gym_card_count.html', {
        'gyms': gym_data
    })

def manage_gym_cards(request):
    gym_cards = GymCard.objects.all()
    return render(request, 'gym/manage_gym_cards.html', {'gym_cards': gym_cards})

@login_required
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

            # Set user to None in GymCard for this card
            GymCard.objects.filter(card_id=nfc_serial, gym=card.gym).update(user=None)

            # Remove gym association from the card
            card.gym = None
            card.save()

            return JsonResponse({'success': True, 'message': 'NFC ID deallocated successfully'})
        except Exception as e:
            logger.error(f"Error in deallocate_gym_nfc: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def manage_gyms(request):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page")
    gyms = Gym.objects.all().select_related('owner')

    # Filter by status
    status = request.GET.get('status')
    if status == 'approved':
        gyms = gyms.filter(is_approved=True)
    elif status == 'unapproved':
        gyms = gyms.filter(is_approved=False)
    # Search by name or owner
    search_query = request.GET.get('search')
    if search_query:
        gyms = gyms.filter(
            Q(venue_name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(pincode__icontains=search_query)
        )
    return render(request, 'gym/manage_gyms.html', {
        'gyms': gyms,
        'status': status,
        'search_query': search_query
    })

@login_required
def toggle_gym_approval(request, gym_id):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to perform this action")
    gym = get_object_or_404(Gym, id=gym_id)
    gym.is_approved = not gym.is_approved
    gym.save()
    return redirect('manage_gyms')

@login_required
@csrf_exempt
def update_gym_subscription_dates(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            gym_id = data.get("gym_id")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            if not gym_id or not start_date or not end_date:
                return JsonResponse({'error': 'Gym ID, start date, and end date are required'}, status=400)
            gym = Gym.objects.get(id=gym_id)
            gym.subscription_start_date = start_date
            gym.subscription_end_date = end_date
            gym.save()
            return JsonResponse({'success': True, 'message': 'Subscription dates updated successfully'})
        except Gym.DoesNotExist:
            return JsonResponse({'error': 'Gym not found'}, status=404)
        except Exception as e:
            logger.error(f"Error in update_gym_subscription_dates: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def gym_dashboard(request, gym_id):
    gym = Gym.objects.annotate(users_count=Count('users')).get(id=gym_id, owner=request.user)

    if request.method == 'POST':
        form = GymUPIForm(request.POST, instance=gym)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'upi_id': gym.upi_id,
                    'recipient_name': gym.recipient_name,
                    'thank_you_message': gym.thank_you_message
                })
            messages.success(request, "UPI details updated successfully!")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': ' '.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
                })
            messages.error(request, "Please correct the errors below.")
    else:
        form = GymUPIForm(instance=gym)

    context = {
        'gym': gym,
        'form': form,
    }
    return render(request, 'gym/gym_dashboard.html', context)

@login_required
def create_gym_subscription_plan(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    plans = GymSubscriptionPlan.objects.filter(gym=gym).order_by('-id')
    if request.method == 'POST':
        form = GymSubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.gym = gym
            plan.save()
            messages.success(request, 'Subscription plan created successfully!')
            return redirect('create_gym_subscription_plan', gym_id=gym_id)
    else:
        form = GymSubscriptionPlanForm()
    return render(request, 'gym/create_subscription_plan.html', {'form': form, 'gym': gym, 'plans': plans})

@login_required
def subscribe_to_gym(request, gym_id, plan_id):
    gym = get_object_or_404(Gym, id=gym_id)
    plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
    if request.method == 'POST':
        form = GymUserSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.subscription = plan
            subscription.save()
            messages.success(request, 'Subscribed successfully!')
            return redirect('gym_dashboard', gym_id=gym_id)
    else:
        form = GymUserSubscriptionForm()
    return render(request, 'gym/subscribe_to_gym.html', {'form': form, 'gym': gym, 'plan': plan})

@login_required
def gym_user_subscriptions(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    subscriptions = GymUserSubscription.objects.filter(subscription__gym=gym)
    return render(request, 'gym/user_subscriptions.html', {'subscriptions': subscriptions, 'gym': gym})

@login_required
def manage_gym_users(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    users = gym.users.all()
    return render(request, 'gym/manage_users.html', {'gym': gym, 'users': users})

@login_required
def nfc_add_gym_user_page(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    # Filter users who have valid subscriptions to this gym and do not have a card allocated
    subscribed_users = GymUserSubscription.objects.filter(
        subscription__gym=gym,
        status='valid'
    ).select_related('user').values_list('user', flat=True).distinct()
    all_users = CustomUser.objects.filter(id__in=subscribed_users).exclude(gymcard__gym=gym)
    if request.method == 'POST':
        card_id = request.POST.get('card_id')
        user_id = request.POST.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            card, created = GymCard.objects.get_or_create(card_id=card_id, gym=gym)
            card.user = user
            card.is_active = True
            card.save()
            gym.users.add(user)
            messages.success(request, f'User {user.get_full_name()} added to gym with card {card_id}')
            return redirect('manage_gym_users', gym_id=gym_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
    return render(request, 'gym/nfc_add_user.html', {'gym': gym, 'all_users': all_users})

@csrf_exempt
@login_required
def check_gym_nfc_allocation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_serial = data.get('nfc_serial')
            gym_id = data.get('gym_id')
            if not nfc_serial or not isinstance(nfc_serial, str):
                return JsonResponse({'error': 'NFC serial must be a string'}, status=400)
            if not gym_id:
                return JsonResponse({'error': 'Gym ID is required'}, status=400)
            try:
                gym = Gym.objects.get(id=gym_id)
            except Gym.DoesNotExist:
                return JsonResponse({'error': 'Gym not found'}, status=404)
            # Check if NFC card is allocated to this gym
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
                if card.gym != gym:
                    return JsonResponse({'error': 'This card is not allocated to this gym'}, status=400)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'Invalid card ID'}, status=400)
            # Check if card is already assigned to a user in GymCard
            try:
                gym_card = GymCard.objects.get(card_id=nfc_serial, gym=gym)
                user = gym_card.user
                if user:
                    return JsonResponse({
                        'allocated': True,
                        'user_full_name': user.get_full_name(),
                        'user_mobile': user.mobile_number,
                        'nfcid': nfc_serial,
                        'timestamp': timezone.now().isoformat()
                    })
                else:
                    return JsonResponse({'allocated': False})
            except GymCard.DoesNotExist:
                return JsonResponse({'allocated': False})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in check_gym_nfc_allocation: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@login_required
def allocate_gym_card(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nfc_serial = data.get('nfc_serial')
            user_id = data.get('user_id')
            gym_id = data.get('gym_id')
            if not nfc_serial or not user_id or not gym_id:
                return JsonResponse({'error': 'NFC serial, user ID, and gym ID are required'}, status=400)
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            try:
                gym = Gym.objects.get(id=gym_id)
            except Gym.DoesNotExist:
                return JsonResponse({'error': 'Gym not found'}, status=404)
            try:
                card = AdminCard.objects.get(card_id=nfc_serial)
                if card.gym != gym:
                    return JsonResponse({'error': 'This card is not allocated to this gym'}, status=400)
            except AdminCard.DoesNotExist:
                return JsonResponse({'error': 'Invalid card ID'}, status=400)
            # Check if user already has a card in this gym
            if GymCard.objects.filter(user=user, gym=gym).exists():
                return JsonResponse({'error': 'This user already has a card allocated in this gym'}, status=400)
            # Check if card is already allocated to another user
            if GymCard.objects.filter(card_id=nfc_serial, gym=gym, user__isnull=False).exists():
                return JsonResponse({'error': 'This card is already allocated to another user'}, status=400)
            # Allocate
            gym_card, created = GymCard.objects.get_or_create(card_id=nfc_serial, gym=gym)
            gym_card.user = user
            gym_card.is_active = True
            gym_card.save()
            gym.users.add(user)
            return JsonResponse({'success': True, 'message': 'User allocated successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in allocate_gym_card: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
def gym_attendance_page(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    return render(request, 'gym/attendance.html', {'gym': gym})

@login_required
def gym_all_attendance(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    attendances = GymAttendance.objects.filter(gym=gym).order_by('-date', '-check_in_time')
    return render(request, 'gym/all_attendance.html', {'gym': gym, 'attendances': attendances})

@login_required
def mark_gym_attendance(request, gym_id):
    if request.method == 'POST':
        nfc_serial = request.POST.get('nfc_id')
        errors = []

        try:
            gym = Gym.objects.get(id=gym_id)
        except Gym.DoesNotExist:
            errors.append('Gym not found')
            return JsonResponse({'errors': errors}, status=400)

        if not gym.is_approved:
            errors.append('Gym is not approved')

        try:
            card = GymCard.objects.get(card_id=nfc_serial, gym=gym)
        except GymCard.DoesNotExist:
            errors.append('Invalid card or not allocated to this gym')
            return JsonResponse({'errors': errors}, status=400)

        if not card.is_active:
            errors.append('Card is not active')

        user = card.user
        if not user:
            errors.append('No user associated with this card')
            return JsonResponse({'errors': errors}, status=400)

        # Check subscription
        if not GymUserSubscription.objects.filter(user=user, subscription__gym=gym, status='valid').exists():
            errors.append('User does not have a valid subscription')

        # Check time
        now = timezone.now()
        if now.time() < gym.opening_time or now.time() > gym.closing_time:
            errors.append('Gym is closed')

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        today = now.date()
        attendance, created = GymAttendance.objects.get_or_create(
            user=user, gym=gym, date=today
        )
        if created or not attendance.check_in_time:
            # Check in
            attendance.check_in_time = now
            attendance.save()
            return JsonResponse({
                'action': 'checkin',
                'message': f'Welcome {user.get_full_name()}!',
                'date': today.strftime('%Y-%m-%d'),
                'time': attendance.check_in_time.strftime('%H:%M:%S')
            })
        elif not attendance.check_out_time:
            # Check out
            attendance.check_out_time = now
            attendance.save()
            return JsonResponse({
                'action': 'checkout',
                'message': f'Goodbye {user.get_full_name()}!',
                'date': today.strftime('%Y-%m-%d'),
                'time': attendance.check_out_time.strftime('%H:%M:%S')
            })
        else:
            return JsonResponse({'errors': ['Already checked out for today']}, status=400)
    return JsonResponse({'errors': ['Invalid request']}, status=400)

@login_required
def gym_expense_dashboard(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    expenses = GymExpense.objects.filter(gym=gym).order_by('-date')
    total_expenses = expenses.aggregate(total=models.Sum('amount'))['total'] or 0
    return render(request, 'gym/expense_dashboard.html', {
        'gym': gym,
        'expenses': expenses,
        'total_expenses': total_expenses
    })

@login_required
def add_gym_expense(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    if request.method == 'POST':
        form = GymExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.gym = gym
            expense.save()
            messages.success(request, 'Expense added successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Expense added successfully!'})
            return redirect('gym_expense_dashboard', gym_id=gym_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = GymExpenseForm()
    return render(request, 'gym/add_expense.html', {'form': form, 'gym': gym})

@login_required
def edit_gym_expense(request, gym_id, expense_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    expense = get_object_or_404(GymExpense, id=expense_id, gym=gym)
    if request.method == 'POST':
        form = GymExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('gym_expense_dashboard', gym_id=gym_id)
    else:
        form = GymExpenseForm(instance=expense)
    return render(request, 'gym/edit_expense.html', {'form': form, 'gym': gym, 'expense': expense})

@login_required
def delete_gym_expense(request, gym_id, expense_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    expense = get_object_or_404(GymExpense, id=expense_id, gym=gym)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('gym_expense_dashboard', gym_id=gym_id)
    return render(request, 'gym/delete_expense.html', {'gym': gym, 'expense': expense})

@login_required
def gym_balance_sheet(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)

    # Calculate total income from valid transactions
    total_income = GymTransaction.objects.filter(
        subscription__gym=gym,
        status='valid'
    ).aggregate(total=models.Sum('amount'))['total'] or 0

    # Calculate total expenses
    total_expenses = GymExpense.objects.filter(gym=gym).aggregate(total=models.Sum('amount'))['total'] or 0

    # Calculate balance
    balance = total_income - total_expenses

    # Get recent transactions and expenses for display
    recent_transactions = GymTransaction.objects.filter(
        subscription__gym=gym,
        status='valid'
    ).order_by('-created_at')[:10]

    recent_expenses = GymExpense.objects.filter(gym=gym).order_by('-date')[:10]

    context = {
        'gym': gym,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'gym/balance_sheet.html', context)

def browse_gyms(request):
    query = request.GET.get('q', '').strip()
    gyms = Gym.objects.filter(is_approved=True)
    if query:
        gyms = gyms.filter(
            models.Q(venue_name__icontains=query) |
            models.Q(address__icontains=query) |
            models.Q(city__icontains=query) |
            models.Q(state__icontains=query) |
            models.Q(district__icontains=query) |
            models.Q(business_type__icontains=query) |
            models.Q(description__icontains=query)
        )
    gyms = gyms.order_by('venue_name')
    return render(request, 'gym/browse_gyms.html', {'gyms': gyms})

@login_required
def gym_graph(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)

    # --- Get all transactions for this gym (from models.py) ---
    all_transactions = GymTransaction.objects.filter(subscription__gym=gym)
    all_expenses = GymExpense.objects.filter(gym=gym)
    all_attendance = GymAttendance.objects.filter(gym=gym)

    # Attendance per day (last 14 days)
    
    today = timezone.now().date()
    days_range = [today - timedelta(days=i) for i in range(13, -1, -1)]
    attendance_labels = [d.strftime('%b %d') for d in days_range]
    attendance_counts = [
        all_attendance.filter(date=d).count() for d in days_range
    ]

    # Revenue per month (last 6 months) using all transactions (valid only)
    

    monthly_revenue_qs = (
        all_transactions.filter(
            status='valid',
            created_at__gte=today - timedelta(days=180)
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=models.Sum('amount'))
        .order_by('month')
    )

    months_labels_full = []
    months_map = OrderedDict()
    for i in range(5, -1, -1):
        dt = (today.replace(day=1) - timedelta(days=i*30))
        label = dt.strftime('%b %Y')
        months_labels_full.append(label)
        months_map[dt.replace(day=1)] = 0
    for item in monthly_revenue_qs:
        key = item['month'].replace(day=1)
        if key in months_map:
            months_map[key] = float(item['revenue'] or 0)
    month_labels = months_labels_full
    monthly_revenue = list(months_map.values())

    context = {
        'gym': gym,
        'attendance_labels': attendance_labels,
        'attendance_counts': attendance_counts,
        'month_labels': month_labels,
        'monthly_revenue': monthly_revenue,
        'all_transactions': all_transactions,
        'all_expenses': all_expenses,
        'all_attendance': all_attendance,
    }
    return render(request, 'gym/charts.html', context)


def gym_details(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, is_approved=True)
    reviews = gym.reviews.select_related('user').all()
    average_rating = gym.average_rating
    subscription_plans = gym.subscription_plans.all()

    # Parse social media links into a list of dicts: [{"url": ..., "display": ...}]
    social_links = []
    if gym.social_media_links:
        for raw_item in gym.social_media_links.split(','):
            s = raw_item.strip()
            if not s:
                continue
            if "|" in s:
                display, url = [x.strip() for x in s.split("|", 1)]
            else:
                url = s
                display = url
            social_links.append({
                "url": url,
                "display": display,
            })

    # Check if user has already reviewed this gym
    user_has_reviewed = gym.reviews.filter(user=request.user).exists()

    if request.method == 'POST' and not user_has_reviewed:
        form = GymReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.gym = gym
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted!')
            return redirect('gym_details', gym_id=gym_id)
    else:
        form = GymReviewForm()

    context = {
        'gym': gym,
        'reviews': reviews,
        'average_rating': average_rating,
        'subscription_plans': subscription_plans,
        'social_links': social_links,
        'form': form,
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'gym/gym_details.html', context)

@login_required
def gym_subscription(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, is_approved=True)
    subscriptions = list(gym.subscription_plans.all())
    coupon_code = request.POST.get('coupon_code') if request.method == 'POST' else None

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        apply_to_all = request.POST.get('apply_to_all')
        if coupon_code and apply_to_all:
            try:
                coupon = GymCoupon.objects.get(code=coupon_code, gym=gym, is_active=True)
                if coupon.is_valid():
                    for plan in subscriptions:
                        if not coupon.applicable_plans.exists() or coupon.applicable_plans.filter(id=plan.id).exists():
                            base_price = plan.discount_price if plan.discount_price else plan.normal_price
                            discounted_price = coupon.apply_discount(base_price)
                            plan.discount_price = discounted_price
                            plan.discount_price_display = f"₹{float(discounted_price):,.2f}"
                            if discounted_price < plan.normal_price:
                                plan.discount_amount = plan.normal_price - discounted_price
                                plan.diff_display = f"₹{plan.discount_amount:.2f} off"
                            else:
                                plan.diff_display = None
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        # AJAX response
                        subscriptions_data = []
                        for plan in subscriptions:
                            subscriptions_data.append({
                                'id': plan.id,
                                'discount_price_display': plan.discount_price_display,
                                'normal_price_display': f"₹{float(plan.normal_price):,.2f}" if plan.normal_price else "-",
                                'diff_display': plan.diff_display,
                            })
                        return JsonResponse({'success': True, 'message': f"Coupon '{coupon_code}' applied successfully!", 'subscriptions': subscriptions_data})
                    else:
                        messages.success(request, f"Coupon '{coupon_code}' applied successfully!")
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': "Coupon is not valid or expired."})
                    else:
                        messages.error(request, "Coupon is not valid or expired.")
            except GymCoupon.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': "Invalid coupon code."})
                else:
                    messages.error(request, "Invalid coupon code.")
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return redirect('gym_subscription', gym_id=gym.id)

    # Enhance subscription plans with display fields
    for plan in subscriptions:
        # Duration display
        months = getattr(plan, 'duration_in_months', None)
        hours = getattr(plan, 'duration_in_hours', None)
        duration_parts = []
        if months:
            duration_parts.append(f"{months} month{'s' if months != 1 else ''}")
        if hours:
            duration_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if duration_parts:
            plan.duration_display = " + ".join(duration_parts)
        else:
            plan.duration_display = "N/A"
        # Price display
        try:
            plan.normal_price_display = f"₹{float(plan.normal_price):,.2f}" if plan.normal_price is not None else "-"
        except Exception:
            plan.normal_price_display = "-"
        try:
            plan.discount_price_display = (
                f"₹{float(plan.discount_price):,.2f}" if plan.discount_price else "-"
            )
        except Exception:
            plan.discount_price_display = "-"
        # Discount displays
        if plan.discount_price and plan.discount_price < plan.normal_price:
            plan.discount_amount = plan.normal_price - plan.discount_price
            plan.diff_display = f"₹{plan.discount_amount:.2f} off"
        else:
            plan.diff_display = None

    context = {
        'gym': gym,
        'subscriptions': subscriptions,
        'coupon_code': coupon_code,
    }
    return render(request, 'gym/gym_subscription.html', context)


# --- REWRITTEN TO CATCH MISSING/MIGRATION ISSUES FOR gym_gymcoupon TABLE ---

@login_required
def gym_coupon_list(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    coupons = GymCoupon.objects.filter(gym=gym)

    if request.method == "POST":
        # Add or update logic, based on POST param "coupon_id"
        coupon_id = request.POST.get("coupon_id")
        if coupon_id:
            try:
                coupon_instance = GymCoupon.objects.get(pk=coupon_id, gym=gym)
                form = GymCouponForm(request.POST, instance=coupon_instance)
                submit_type = "edit"
            except GymCoupon.DoesNotExist:
                form = GymCouponForm(request.POST, initial={'gym': gym, 'created_by': request.user})
                submit_type = "create"
        else:
            form = GymCouponForm(request.POST, initial={'gym': gym, 'created_by': request.user})
            submit_type = "create"

        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.gym = gym
            if not coupon_id:
                coupon.created_by = request.user
            coupon.save()
            if 'applicable_plans' in form.cleaned_data:
                coupon.applicable_plans.set(form.cleaned_data['applicable_plans'])
            else:
                coupon.applicable_plans.clear()
            if submit_type == "edit":
                messages.success(request, "Coupon updated successfully!")
            else:
                messages.success(request, "Coupon created successfully!")
            return redirect('gym_coupon_list', gym_id=gym.id)
    else:
        form = GymCouponForm(initial={'gym': gym, 'created_by': request.user})

    return render(request, 'gym/gym_coupon_list.html', {
        'gym': gym,
        'coupons': coupons,
        'form': form,
    })


@login_required
def gym_coupon_data(request, coupon_id):
    try:
        coupon = GymCoupon.objects.get(pk=coupon_id)
        # Check if user owns the gym
        if coupon.gym.owner != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        data = {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'max_usage': coupon.max_usage,
            'valid_from': coupon.valid_from.strftime('%Y-%m-%dT%H:%M'),
            'valid_to': coupon.valid_to.strftime('%Y-%m-%dT%H:%M'),
            'is_active': coupon.is_active,
            'applicable_plans': list(coupon.applicable_plans.values_list('id', flat=True)),
        }
        return JsonResponse(data)
    except GymCoupon.DoesNotExist:
        return JsonResponse({'error': 'Coupon not found'}, status=404)

@login_required
def gym_payment_page(request, gym_id, plan_id):
    gym = get_object_or_404(Gym, id=gym_id, is_approved=True)
    plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
    coupon_code = request.POST.get('coupon_code', '')

    # Calculate final amount
    final_amount = plan.discount_price if plan.discount_price else plan.normal_price
    if coupon_code:
        try:
            coupon = GymCoupon.objects.get(code=coupon_code, gym=gym, is_active=True)
            if coupon.is_valid() and (not coupon.applicable_plans.exists() or coupon.applicable_plans.filter(id=plan.id).exists()):
                final_amount = coupon.apply_discount(final_amount)
        except GymCoupon.DoesNotExist:
            pass  # Ignore invalid coupon

    # Generate QR code for UPI
    qr_code_url = None
    if gym.upi_id:

        upi_string = f"upi://pay?pa={gym.upi_id}&pn={gym.recipient_name}&am={final_amount}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_string)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    context = {
        'gym': gym,
        'plan': plan,
        'final_amount': final_amount,
        'coupon_code': coupon_code,
        'qr_code_url': qr_code_url,
    }
    return render(request, 'gym/gym_payment.html', context)

@login_required
def gym_payment_success(request, gym_id, plan_id):
    gym = get_object_or_404(Gym, id=gym_id, is_approved=True)
    plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '')
        final_amount = request.POST.get('final_amount')
        transaction_id = request.POST.get('transaction_id')
        payment_mode = request.POST.get('payment_mode')

        # Calculate final amount again to verify
        amount = plan.discount_price if plan.discount_price else plan.normal_price
        coupon = None
        if coupon_code:
            try:
                coupon = GymCoupon.objects.get(code=coupon_code, gym=gym, is_active=True)
                if coupon.is_valid() and (not coupon.applicable_plans.exists() or coupon.applicable_plans.filter(id=plan.id).exists()):
                    amount = coupon.apply_discount(amount)
            except GymCoupon.DoesNotExist:
                coupon = None

        if float(final_amount) != amount:
            messages.error(request, "Amount mismatch. Please try again.")
            return redirect('gym_subscription', gym_id=gym.id)

        # Create transaction
        transaction = GymTransaction.objects.create(
            user=request.user,
            subscription=plan,
            transaction_id=transaction_id,
            amount=amount,
            status='pending'
        )

        # Increment `times_used` if coupon was used
        if coupon is not None:
            coupon.increment_usage()

        context = {
            'gym': gym,
            'transaction_id': transaction_id,
        }
        return render(request, 'gym/payment_success.html', context)

    return redirect('gym_subscription', gym_id=gym.id)

@csrf_exempt
@login_required
@require_POST
def gym_coupon_delete(request, gym_id, coupon_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    try:
        coupon = GymCoupon.objects.get(pk=coupon_id, gym=gym)
        coupon.delete()
        return JsonResponse({'success': True, 'message': "Coupon deleted successfully!"})
    except GymCoupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Coupon not found."}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

