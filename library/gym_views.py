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

from .models import Gym, GymProfileImage, GymCoupon, GymBanner
from .forms import GymRegistrationForm, GymProfileImageForm, GymEditForm, GymCouponForm, GymBannerForm
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
    active_coupon_count = GymCoupon.objects.filter(gym=gym, status='ACTIVE').count()
    total_coupon_count = GymCoupon.objects.filter(gym=gym).count()
    return render(request, 'gym/gym_dashboard.html', {
        'gym': gym, 
        'active_coupon_count': active_coupon_count,
        'total_coupon_count': total_coupon_count
    })

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

@login_required
def manage_gym_coupons(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if gym.owner != request.user:
        raise PermissionDenied("You do not have permission to manage coupons for this gym.")

    if request.method == 'GET' and 'id' in request.GET:
        coupon = get_object_or_404(GymCoupon, pk=request.GET['id'], gym=gym)
        data = {
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'valid_from': coupon.valid_from.strftime('%Y-%m-%dT%H:%M'),
            'valid_to': coupon.valid_to.strftime('%Y-%m-%dT%H:%M'),
            'max_usage': coupon.max_usage,
            'status': coupon.status,
        }
        return JsonResponse(data)

    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        instance = None
        if coupon_id:
            instance = get_object_or_404(GymCoupon, pk=coupon_id, gym=gym)
        
        form = GymCouponForm(request.POST, instance=instance)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.gym = gym
            coupon.save()
            return JsonResponse({'success': True, 'message': 'Coupon saved successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)

    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            coupon = get_object_or_404(GymCoupon, pk=data['id'], gym=gym)
            coupon.delete()
            return JsonResponse({'success': True, 'message': 'Coupon deleted successfully!'})
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    coupons = GymCoupon.objects.filter(gym=gym).order_by('-created_at')
    form = GymCouponForm()

    context = {
        'gym': gym,
        'coupons': coupons,
        'form': form,
    }
    return render(request, 'gym/manage_gym_coupons.html', context)

@login_required
def manage_gym_banners(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if gym.owner != request.user:
        raise PermissionDenied("You do not have permission to manage banners for this gym.")
    banners = gym.banners.order_by('-created_at')
    max_banners = gym.max_banners or 2
    if request.method == 'POST':
        form = GymBannerForm(request.POST)
        if form.is_valid():
            if gym.banners.count() >= max_banners:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': f"Maximum {max_banners} banners allowed for this gym."})
                form.add_error(None, f"Maximum {max_banners} banners allowed for this gym.")
            else:
                banner = form.save(commit=False)
                banner.gym = gym
                banner.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                messages.success(request, 'Banner added successfully!')
                return redirect('manage_gym_banners', gim_uid=gym.gim_uid)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    else:
        form = GymBannerForm()
    # AJAX partial rendering for banners list
    if request.GET.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('gym/manage_gym_banners.html', { 'gym': gym, 'banners': banners, 'form': form, 'max_banners': max_banners })
        from django.http import HttpResponse
        return HttpResponse(html)
    context = {
        'gym': gym,
        'banners': banners,
        'form': form,
        'max_banners': max_banners,
    }
    return render(request, 'gym/manage_gym_banners.html', context)

@require_POST
@login_required
def remove_gym_banner(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if gym.owner != request.user:
        raise PermissionDenied("You do not have permission to remove banners for this gym.")
    banner_id = request.POST.get('banner_id')
    if banner_id:
        banner = get_object_or_404(gym.banners, id=banner_id)
        banner.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Banner removed successfully!')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid banner ID.'})
        messages.error(request, 'Invalid banner ID.')
    return redirect('manage_gym_banners', gim_uid=gym.gim_uid)