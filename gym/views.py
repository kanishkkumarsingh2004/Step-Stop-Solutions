
from django.shortcuts import render, redirect, get_object_or_404
from .models import Gym, GymCard, GymAttendance, GymSubscriptionPlan, GymUserSubscription, GymTransaction, GymExpense
from .forms import GymForm, GymRegistrationForm, GymUPIForm, GymSubscriptionPlanForm, GymUserSubscriptionForm, GymTransactionForm, GymExpenseForm
from library.models import AdminCard, CustomUser
from django.contrib import messages
from django.db import models, transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import json
import logging

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
    if request.method == 'POST':
        form = GymSubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.gym = gym
            plan.save()
            messages.success(request, 'Subscription plan created successfully!')
            return redirect('gym_dashboard', gym_id=gym_id)
    else:
        form = GymSubscriptionPlanForm()
    return render(request, 'gym/create_subscription_plan.html', {'form': form, 'gym': gym})

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
