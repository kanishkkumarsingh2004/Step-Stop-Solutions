from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods, require_GET
import re
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
import json
import base64
from io import BytesIO
from datetime import timedelta
import qrcode
from collections import defaultdict
from django.contrib import messages
# Django core imports
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django.utils.safestring import mark_safe

from .models import Gym, GymProfileImage, GymCoupon, GymBanner, GymSubscriptionPlan, GymSubscription, GymCardLog, AdminCard, GymExpense
from .forms import GymRegistrationForm, GymProfileImageForm, GymEditForm, GymCouponForm, GymBannerForm, GymSubscriptionPlanForm, GymSubscriptionPublicPaymentForm, GymExpenseForm
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
            'applicable_plans': [p.id for p in coupon.applicable_plans.all()],
        }
        return JsonResponse(data)

    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        instance = None
        if coupon_id:
            instance = get_object_or_404(GymCoupon, pk=coupon_id, gym=gym)
        form = GymCouponForm(request.POST, instance=instance, gym=gym)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.gym = gym
            coupon.save()
            form.save_m2m()
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
    form = GymCouponForm(gym=gym)

    # Determine selected_plan_ids for the template (for GET page load)
    selected_plan_ids = []
    if form.is_bound:
        selected_plan_ids = [int(pid) for pid in form.data.getlist('applicable_plans')]
    elif form.instance.pk:
        selected_plan_ids = list(form.instance.applicable_plans.values_list('id', flat=True))

    context = {
        'gym': gym,
        'coupons': coupons,
        'form': form,
        'selected_plan_ids': selected_plan_ids,
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

@login_required
def manage_gym_subscription_plans(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        if plan_id:
            plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
            form = GymSubscriptionPlanForm(request.POST, instance=plan)
        else:
            form = GymSubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.gym = gym
            plan.save()
            return JsonResponse({'success': True, 'message': 'Plan saved successfully.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        plan_id = request.GET.get('plan_id')
        if plan_id:
            plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
            data = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'duration_in_months': plan.duration_in_months,
                'duration_in_hours': plan.duration_in_hours,
                'price': str(plan.price),
                'discount_price': str(plan.discount_price) if plan.discount_price else '',
            }
            return JsonResponse(data)
        else:
            plans = gym.subscription_plans.all().order_by('-created_at')
            plans_data = [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'duration_in_months': p.duration_in_months,
                    'duration_in_hours': p.duration_in_hours,
                    'price': str(p.price),
                    'discount_price': str(p.discount_price) if p.discount_price else '',
                } for p in plans
            ]
            return JsonResponse({'plans': plans_data})

    # Default: render management page
    plans = gym.subscription_plans.all().order_by('-created_at')
    form = GymSubscriptionPlanForm()
    return render(request, 'gym/manage_gym_subscription_plans.html', {
        'gym': gym,
        'plans': plans,
        'form': form,
    })

def public_gym_subscription_plans(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, is_approved=True)
    plans = gym.subscription_plans.all().order_by('price')
    return render(request, 'gym/public_gym_subscription_plans.html', {
        'gym': gym,
        'plans': plans,
    })

@require_POST
def ajax_apply_gym_coupon(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, is_approved=True)
    code = request.POST.get('coupon_code', '').strip()
    plan_id = request.POST.get('plan_id')
    response = {'success': False, 'message': '', 'discounts': {}}
    if not code:
        response['message'] = 'Please enter a coupon code.'
        return JsonResponse(response)
    try:
        coupon = GymCoupon.objects.get(gym=gym, code__iexact=code, status='ACTIVE')
    except GymCoupon.DoesNotExist:
        response['message'] = 'Invalid or expired coupon.'
        return JsonResponse(response)
    if not coupon.is_valid():
        response['message'] = 'This coupon is not valid or has expired.'
        return JsonResponse(response)
    # If plan_id is provided, only apply to that plan
    if plan_id:
        try:
            plan = gym.subscription_plans.get(id=plan_id)
        except GymSubscriptionPlan.DoesNotExist:
            response['message'] = 'Invalid plan.'
            return JsonResponse(response)
        if not coupon.is_applicable_to_plan(plan):
            response['message'] = 'This coupon is not valid for the selected plan.'
            return JsonResponse(response)
        original_price = plan.discount_price if plan.has_discount else plan.price
        discounted = coupon.apply_discount(original_price)
        response['discounts'][plan.id] = float(discounted)
        response['success'] = True
        response['message'] = f'Coupon "{code}" applied!'
        return JsonResponse(response)
    # Otherwise, apply to all plans as before (for backward compatibility)
    plans = gym.subscription_plans.all()
    for plan in plans:
        if coupon.is_applicable_to_plan(plan):
            original_price = plan.discount_price if plan.has_discount else plan.price
            discounted = coupon.apply_discount(original_price)
            response['discounts'][plan.id] = float(discounted)
    response['success'] = True
    response['message'] = f'Coupon "{code}" applied!'
    return JsonResponse(response)

def public_gym_subscription_payment(request, gim_uid, plan_id):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, is_approved=True)
    plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
    user = request.user if request.user.is_authenticated else None
    form = GymSubscriptionPublicPaymentForm(request.POST or None)
    original_price = plan.discount_price if plan.has_discount else plan.price
    discounted_price = original_price
    coupon_obj = None
    coupon_error = None
    coupon_code = None
    discount_amount = 0

    def handle_coupon(code):
        nonlocal coupon_obj, coupon_error, discounted_price, discount_amount
        try:
            coupon_obj = GymCoupon.objects.get(gym=gym, code__iexact=code, status='ACTIVE')
            if not coupon_obj.is_valid() or not coupon_obj.is_applicable_to_plan(plan):
                coupon_error = 'Invalid or inapplicable coupon.'
                coupon_obj = None
            else:
                discounted_price = coupon_obj.apply_discount(original_price)
                discount_amount = original_price - discounted_price
        except GymCoupon.DoesNotExist:
            coupon_error = 'Invalid coupon code.'
            coupon_obj = None

    # Handle GET request with coupon
    if request.method == 'GET':
        coupon_code = request.GET.get('coupon', '').strip()
        if coupon_code:
            handle_coupon(coupon_code)

    # Handle POST request
    elif request.method == 'POST' and form.is_valid():
        payment_method = form.cleaned_data['payment_method']
        transaction_id = form.cleaned_data['transaction_id']
        coupon_code = form.cleaned_data['coupon_code'].strip() if form.cleaned_data['coupon_code'] else None
        
        # Apply coupon if provided
        if coupon_code:
            handle_coupon(coupon_code)
        
        # Generate transaction_id for cash if not provided
        if payment_method == 'cash' and (not transaction_id or transaction_id.strip() == ''):
            transaction_id = f"CASH-{user.id}-{int(time.time())}"
        
        # Redirect to login if user is not authenticated
        if not user:
            return redirect('%s?next=%s' % (reverse('login'), request.path))
        
        # Create subscription
        from datetime import date, timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=plan.duration_in_months*30)
        subscription = GymSubscription.objects.create(
            user=user,
            subscription_plan=plan,
            start_date=start_date,
            end_date=end_date,
            amount_paid=discounted_price,
            payment_method=payment_method,
            transaction_id=transaction_id,
            coupon_applied=coupon_obj if coupon_obj else None,
        )
        
        # Use coupon if applied
        if coupon_obj:
            coupon_obj.use_coupon()
        
        return redirect('public_gym_subscription_success', gim_uid=gym.gim_uid, plan_id=plan.id)
    # UPI QR code
    upi_url = None
    qr_code_base64 = None
    if gym.upi_id and gym.recipient_name:
        upi_url = f"upi://pay?pa={gym.upi_id}&pn={gym.recipient_name}&am={discounted_price}&cu=INR&tn=Gym Subscription Payment"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return render(request, 'gym/public_gym_subscription_payment.html', {
        'gym': gym,
        'plan': plan,
        'form': form,
        'discounted_price': discounted_price,
        'original_price': original_price,
        'discount_amount': discount_amount,
        'upi_url': upi_url,
        'qr_code_base64': qr_code_base64,
        'coupon_error': coupon_error,
        'coupon_code': coupon_code,
    })

def public_gym_subscription_success(request, gim_uid, plan_id):
    gym = get_object_or_404(Gym, gim_uid=gim_uid, is_approved=True)
    plan = get_object_or_404(GymSubscriptionPlan, id=plan_id, gym=gym)
    return render(request, 'gym/public_gym_subscription_success.html', {
        'gym': gym,
        'plan': plan,
    })

@login_required
def gym_verify_payments(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        sub_id = request.POST.get('subscription_id')
        new_status = request.POST.get('payment_status')
        if not sub_id or new_status not in ['pending', 'valid', 'invalid']:
            return JsonResponse({'success': False, 'message': 'Invalid data.'}, status=400)
        try:
            sub = GymSubscription.objects.get(id=sub_id, subscription_plan__gym=gym)
            sub.payment_status = new_status
            sub.save(update_fields=['payment_status'])
            return JsonResponse({'success': True, 'message': 'Payment status updated.'})
        except GymSubscription.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Subscription not found.'}, status=404)
    # GET: show all subscriptions for this gym
    subscriptions = GymSubscription.objects.filter(subscription_plan__gym=gym).select_related('user', 'subscription_plan').order_by('-created_at')
    return render(request, 'gym/gym_verify_payments.html', {
        'gym': gym,
        'subscriptions': subscriptions,
    })

@login_required
def manage_gym_enrolled_users(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    # Get all subscriptions for this gym
    subscriptions = GymSubscription.objects.filter(subscription_plan__gym=gym).select_related('user', 'subscription_plan').order_by('-created_at')
    # Unique users with their latest subscription
    user_map = {}
    for sub in subscriptions:
        if sub.user_id not in user_map:
            user_map[sub.user_id] = sub
    enrolled_users = [sub for sub in user_map.values()]
    return render(request, 'gym/manage_gym_enrolled_users.html', {
        'gym': gym,
        'enrolled_users': enrolled_users,
        'total_enrolled': len(enrolled_users),
    })

@login_required
def allocate_gym_card_page(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner:
        raise PermissionDenied("You do not have permission to allocate cards for this gym.")
    # Get all enrolled users
    subscriptions = GymSubscription.objects.filter(subscription_plan__gym=gym).select_related('user').order_by('-created_at')
    user_map = {}
    for sub in subscriptions:
        if sub.user_id not in user_map:
            user_map[sub.user_id] = sub.user
    enrolled_users = list(user_map.values())
    # Get available admin cards (not allocated to any gym)
    allocated_card_ids = set(GymCardLog.objects.filter(gym=gym).values_list('card_id', flat=True))
    available_cards = AdminCard.objects.filter(gym__isnull=True, library__isnull=True, institution__isnull=True)
    # Get allocated card info for users
    user_card_logs = GymCardLog.objects.filter(gym=gym, user__in=enrolled_users)
    allocated_card_ids = set(log.user_id for log in user_card_logs)
    allocated_card_map = {log.user_id: log.card_id for log in user_card_logs}
    return render(request, 'gym/allocate_gym_card.html', {
        'gym': gym,
        'enrolled_users': enrolled_users,
        'available_cards': available_cards,
        'allocated_card_ids': allocated_card_ids,
        'allocated_card_map': allocated_card_map,
    })

@require_POST
@login_required
def ajax_allocate_gym_card(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner:
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
    user_id = request.POST.get('user_id')
    card_id = request.POST.get('card_id')
    if not user_id or not card_id:
        return JsonResponse({'success': False, 'message': 'Missing user or card.'}, status=400)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    card = get_object_or_404(AdminCard, card_id=card_id, gym__isnull=True, library__isnull=True, institution__isnull=True)
    # Prevent duplicate allocation
    if GymCardLog.objects.filter(gym=gym, user=user, card_id=card_id).exists():
        return JsonResponse({'success': False, 'message': 'Card already allocated to this user.'}, status=400)
    GymCardLog.objects.create(gym=gym, user=user, card_id=card_id, allocated_by=request.user)
    # Mark card as allocated
    card.gym = gym
    card.save(update_fields=['gym'])
    return JsonResponse({'success': True, 'message': 'Card allocated successfully.'})

@login_required
def gym_expense_dashboard(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to view this gym's expenses.")
    expenses = GymExpense.objects.filter(gym=gym).order_by('-date', '-created_at')
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    form = GymExpenseForm()
    return render(request, 'gym/gym_expense_dashboard.html', {
        'gym': gym,
        'expenses': expenses,
        'total_expenses': total_expenses,
        'form': form,
    })

@login_required
@require_POST
@csrf_exempt
def add_gym_expense(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
    form = GymExpenseForm(request.POST)
    if form.is_valid():
        expense = form.save(commit=False)
        expense.gym = gym
        expense.save()
        return JsonResponse({'success': True, 'message': 'Expense added successfully.'})
    else:
        return JsonResponse({'success': False, 'message': ' '.join([str(e) for e in form.errors.values()])}, status=400)

@login_required
def gym_balance_sheet(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to view this gym's balance sheet.")
    expenses = GymExpense.objects.filter(gym=gym).order_by('date', 'created_at')
    from .models import GymSubscription
    profits = GymSubscription.objects.filter(
        subscription_plan__gym=gym,
        payment_status='valid'
    ).order_by('created_at')
    # Build a unified list of transactions
    txn_list = []
    for exp in expenses:
        txn_list.append({
            'date': exp.date,
            'type': 'loss',
            'description': exp.expense_description or exp.expense_name,
            'amount': exp.amount,
            'sort_time': exp.created_at,
        })
    for sub in profits:
        txn_list.append({
            'date': sub.created_at.date(),
            'type': 'profit',
            'description': f"Subscription payment by {sub.user.get_full_name()} ({sub.subscription_plan.name})",
            'amount': sub.amount_paid,
            'sort_time': sub.created_at,
        })
    # Sort all transactions by date and time
    txn_list.sort(key=lambda x: (x['date'], x['sort_time']))
    # Calculate running balance, total profit, total loss
    balance = 0
    total_profit = 0
    total_loss = 0
    transactions = []
    for txn in txn_list:
        if txn['type'] == 'profit':
            balance += txn['amount']
            total_profit += txn['amount']
        else:
            balance -= txn['amount']
            total_loss += txn['amount']
        transactions.append({
            'date': txn['date'],
            'type': txn['type'],
            'description': txn['description'],
            'amount': txn['amount'],
            'balance': balance,
        })
    net_balance = total_profit - total_loss
    context = {
        'gym': gym,
        'transactions': transactions,
        'total_profit': total_profit,
        'total_loss': total_loss,
        'net_balance': net_balance,
    }
    return render(request, 'gym/gym_balance_sheet.html', context)

@login_required
def gym_analytics_page(request, gim_uid):
    gym = get_object_or_404(Gym, gim_uid=gim_uid)
    if request.user != gym.owner and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to view this gym's analytics.")
    # Get all valid profits (subscriptions) and all expenses
    from .models import GymSubscription, GymExpense
    profits = GymSubscription.objects.filter(subscription_plan__gym=gym, payment_status='valid').order_by('created_at')
    expenses = GymExpense.objects.filter(gym=gym).order_by('date', 'created_at')
    # 1. Income vs Expenses Over Time (by date)
    date_income = defaultdict(float)
    date_expense = defaultdict(float)
    for sub in profits:
        date_income[sub.created_at.date()] += float(sub.amount_paid)
    for exp in expenses:
        date_expense[exp.date] += float(exp.amount)
    all_dates = sorted(set(date_income.keys()) | set(date_expense.keys()))
    income_expense_data = {
        'labels': [d.strftime('%Y-%m-%d') for d in all_dates],
        'income': [date_income[d] for d in all_dates],
        'expenses': [date_expense[d] for d in all_dates],
    }
    # 2. Profit vs Loss Pie
    total_profit = sum(float(sub.amount_paid) for sub in profits)
    total_loss = sum(float(exp.amount) for exp in expenses)
    profit_loss_data = {
        'profit': total_profit,
        'loss': total_loss,
    }
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for sub in profits:
        key = sub.created_at.strftime('%Y-%m')
        monthly_income[key] += float(sub.amount_paid)
    for exp in expenses:
        key = exp.date.strftime('%Y-%m')
        monthly_expense[key] += float(exp.amount)
    all_months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))
    monthly_trend_data = {
        'labels': all_months,
        'income': [monthly_income[m] for m in all_months],
        'expenses': [monthly_expense[m] for m in all_months],
    }
    # 4. Payment Method Breakdown
    payment_method_map = defaultdict(float)
    for sub in profits:
        if sub.payment_method:
            payment_method_map[sub.payment_method] += float(sub.amount_paid)
    for exp in expenses:
        if exp.payment_mode:
            payment_method_map[exp.payment_mode] -= float(exp.amount)
    payment_method_data = {
        'labels': list(payment_method_map.keys()),
        'amounts': [payment_method_map[k] for k in payment_method_map.keys()],
    }
    # 5. Expense Category Bar
    expense_category_map = defaultdict(float)
    for exp in expenses:
        if exp.expense_name:
            expense_category_map[exp.expense_name] += float(exp.amount)
    expense_category_data = {
        'labels': list(expense_category_map.keys()),
        'amounts': [expense_category_map[k] for k in expense_category_map.keys()],
    }
    # 6. Cumulative Balance Over Time
    txn_list = []
    for exp in expenses:
        txn_list.append({'date': exp.date, 'type': 'loss', 'amount': float(exp.amount), 'sort_time': exp.created_at})
    for sub in profits:
        txn_list.append({'date': sub.created_at.date(), 'type': 'profit', 'amount': float(sub.amount_paid), 'sort_time': sub.created_at})
    txn_list.sort(key=lambda x: (x['date'], x['sort_time']))
    cum_balance = 0
    cum_labels = []
    cum_balances = []
    for txn in txn_list:
        if txn['type'] == 'profit':
            cum_balance += txn['amount']
        else:
            cum_balance -= txn['amount']
        cum_labels.append(txn['date'].strftime('%Y-%m-%d'))
        cum_balances.append(cum_balance)
    cumulative_balance_data = {
        'labels': cum_labels,
        'balances': cum_balances,
    }

    context = {
        'gym': gym,
        'income_expense_data': json.dumps(income_expense_data),
        'profit_loss_data': json.dumps(profit_loss_data),
        'monthly_trend_data': json.dumps(monthly_trend_data),
        'payment_method_data': json.dumps(payment_method_data),
        'expense_category_data': json.dumps(expense_category_data),
        'cumulative_balance_data': json.dumps(cumulative_balance_data),
        'total_profit': total_profit,
        'total_loss': total_loss,
        'net_balance': float(total_profit - total_loss)


    }
    return render(request, 'gym/gym_analytics.html', context)