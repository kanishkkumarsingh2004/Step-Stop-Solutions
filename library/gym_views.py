from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.core.paginator import Paginator
import re
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Sum
import json
from decimal import Decimal
import decimal
import base64
from io import BytesIO
from datetime import timedelta
import qrcode
from collections import defaultdict
from django.contrib import messages
# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now

from .models import Gym, GymProfileImage
from .forms import GymRegistrationForm, GymProfileImageForm, GymEditForm
# In my_library/library/views.py


def search_gyms(request):
    query = request.GET.get('q', '')
    gyms = Gym.objects.filter(is_approved=True)
    if query:
        gyms = gyms.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(owner__first_name__icontains=query) |
            Q(owner__last_name__icontains=query)
        )
    return render(request, 'gym/search_gyms.html', {'gyms': gyms})

@login_required
def register_gym(request):
    """Register a new gym."""
    if request.method == 'POST':
        form = GymRegistrationForm(request.POST)
        if form.is_valid():
            gym = form.save(commit=False)
            gym.owner = request.user
            gym.save()
            messages.success(request, 'Gym registration submitted successfully! It will be reviewed by our team.')
            return redirect('gym_registration_success')
    else:
        form = GymRegistrationForm()
    
    return render(request, 'gym/register_gym.html', {'form': form})

def gym_registration_success(request):
    """Display a success message after gym registration."""
    return render(request, 'gym/registration_success.html')

def gym_details(request, gim_uid):
    """Display the details of a specific gym."""
    gym = get_object_or_404(Gym, gim_uid=gim_uid, is_approved=True)
    return render(request, 'gym/gym_details.html', {'gym': gym})

@login_required
def gym_dashboard(request, gim_uid):
    """Display the dashboard for a specific gym."""
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if gym.owner != request.user:
        raise PermissionDenied("You do not have permission to view this dashboard.")
    
    return render(request, 'gym/gym_dashboard.html', {'gym': gym})

@require_POST
@login_required
def upload_gym_profile_image(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, owner=request.user)
    form = GymProfileImageForm(request.POST)
    if form.is_valid():
        profile_image, created = GymProfileImage.objects.get_or_create(gym=gym)
        profile_image.google_drive_link = form.cleaned_data['google_drive_link']
        profile_image.save()
        return JsonResponse({'success': True, 'image_url': profile_image.google_drive_link})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
@login_required
def remove_gym_profile_image(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, owner=request.user)
    if hasattr(gym, 'profile_image'):
        gym.profile_image.delete()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No profile image found.'}, status=404)

@login_required
def edit_gym_profile(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, owner=request.user)
    if request.method == 'POST':
        form = GymEditForm(request.POST, instance=gym)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gym profile updated successfully!')
            return redirect('gym_dashboard', gim_uid=gym.gim_uid)
    else:
        form = GymEditForm(instance=gym)
    return render(request, 'gym/edit_gym_profile.html', {'form': form, 'gym': gym})

@require_POST
@login_required
def update_gym_upi_details(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, owner=request.user)
    upi_id = request.POST.get('upi_id', '').strip()
    recipient_name = request.POST.get('recipient_name', '').strip()
    thank_you_message = request.POST.get('thank_you_message', '').strip()
    gym.upi_id = upi_id
    gym.recipient_name = recipient_name
    gym.thank_you_message = thank_you_message
    gym.save()
    return JsonResponse({
        'success': True,
        'upi_id': gym.upi_id,
        'recipient_name': gym.recipient_name,
        'thank_you_message': gym.thank_you_message,
    })