from django.shortcuts import render, redirect, get_object_or_404
from .models import Gym, GymCard
from .forms import GymForm, GymRegistrationForm
from library.models import AdminCard, CustomUser
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
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
            return redirect('dashboard')
    else:
        form = GymRegistrationForm()
    return render(request, 'gym/register_gym.html', {'form': form})

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
def gym_dashboard(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, owner=request.user)
    context = {
        'gym': gym,
    }
    return render(request, 'gym/gym_dashboard.html', context)
