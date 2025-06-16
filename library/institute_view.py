# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from .forms import InstitutionRegistrationForm, InstitutionCouponForm, UPIForm, InstitutionBannerForm, InstitutionSubscriptionPlanForm
from django.contrib import messages
from .models import Institution, CustomUser, InstitutionCoupon, InstitutionReview, InstitutionImage, InstitutionBanner, InstitutionSubscriptionPlan, InstitutionSubscription   
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.db import models
import re
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
import json
from decimal import Decimal
import decimal
import base64
from io import BytesIO
from datetime import timedelta
import qrcode

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def coaching_dashboard(request, uid):
    """Display the coaching dashboard for the institution owner."""
    try:
        institution = get_object_or_404(Institution, uid=uid)
        
        # Check if the user is the owner of the institution
        if request.user != institution.owner:
            messages.error(request, "You don't have permission to access this dashboard.")
            return redirect('home')
        
        # Calculate coupon counts
        active_coupons_count = institution.coupons.filter(status='ACTIVE').count()
        total_coupons_count = institution.coupons.count()
        expired_coupons_count = institution.coupons.filter(status='EXPIRED').count()
        
        # Get the first institution image
        first_image = institution.images.first()
        return render(request, 'coaching/coaching_dashboard.html', {
            'institution': institution,
            'active_coupons_count': active_coupons_count,
            'total_coupons_count': total_coupons_count,
            'expired_coupons_count': expired_coupons_count,
            'primary_image': first_image  # Keep the variable name for template compatibility
        })
    except Institution.DoesNotExist:
        messages.error(request, "Institution not found.")
        return redirect('home')

@login_required
def register_coaching_form(request):
    """Handle coaching center registration"""
    if request.method == 'POST':
        form = InstitutionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                institution = form.save(commit=False)
                institution.owner = request.user
                institution.business_type = 'Institution'
                institution.save()
                messages.success(request, "Institute registered successfully!")
                return redirect('enrollment_success_coaching')
            except Exception as e:
                logger.error(f"Error saving institution: {str(e)}")
                messages.error(request, "An error occurred while saving the institution. Please try again.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = InstitutionRegistrationForm()
    
    return render(request, 'coaching/register_coaching_form.html', {'form': form})

def enrollment_success(request):
    """Show success page after enrollment"""
    return render(request, 'coaching/enrollment_success.html')

@login_required
def institution_details(request, uid):
    """View institution details"""
    institution = get_object_or_404(Institution, uid=uid)
    
    return render(request, 'coaching/institution_details.html', {
        'institution': institution,
    })

def public_institute_details(request, uid):
    """Public view of institution details"""
    institution = get_object_or_404(Institution, uid=uid)
    images = InstitutionImage.objects.filter(institution=institution).first()  # Get images for this particular institution
    if not institution.is_approved:
        messages.error(request, "This institution is not yet approved.")
        return redirect('home')
    return render(request, 'coaching/public_institute_details.html', {
        'institution': institution,
        'images': images,
    })

@login_required
@require_POST
def approve_institution(request, uid):
    """Approve an institution"""
    try:
        institution = get_object_or_404(Institution, uid=uid)
        institution.is_approved = True
        institution.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Institution approved successfully',
            'is_approved': True
        })
    except Exception as e:
        logger.error(f"Error approving institution: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to approve institution'
        }, status=400)

@login_required
@require_POST
def unapprove_institution(request, uid):
    """Unapprove an institution"""
    try:
        institution = get_object_or_404(Institution, uid=uid)
        institution.is_approved = False
        institution.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Institution unapproved successfully',
            'is_approved': False
        })
    except Exception as e:
        logger.error(f"Error unapproving institution: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to unapprove institution'
        }, status=400)

@login_required
def edit_institution_profile(request, uid):
    """Edit institution profile"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to edit this institution.")
        return redirect('coaching_dashboard', uid=institution.uid)
    
    if request.method == 'POST':
        form = InstitutionRegistrationForm(request.POST, instance=institution)
        if form.is_valid():
            try:
                # Save the basic form data
                institution = form.save(commit=False)
                
                # Start with existing classrooms
                classrooms = institution.classrooms or {}
                
                # Process existing classrooms
                for key, value in request.POST.items():
                    if key.startswith('classroom_') and '_name' in key:
                        classroom_id = key.split('_')[1]
                        capacity_key = f'classroom_{classroom_id}_capacity'
                        if capacity_key in request.POST:
                            try:
                                capacity = int(request.POST[capacity_key])
                                if capacity < 1:
                                    raise ValueError("Capacity must be at least 1")
                                classrooms[f'classroom_{classroom_id}'] = {
                                    'name': value,
                                    'capacity': capacity
                                }
                            except ValueError as e:
                                messages.error(request, f"Invalid capacity for classroom {value}: {str(e)}")
                                return render(request, 'coaching/edit_institution_profile.html', {
                                    'form': form,
                                    'institution': institution
                                })
                
                # Process new classrooms
                new_names = request.POST.getlist('classroom_new_name[]')
                new_capacities = request.POST.getlist('classroom_new_capacity[]')
                
                for i, (name, capacity) in enumerate(zip(new_names, new_capacities)):
                    if name and capacity:  # Only add if both name and capacity are provided
                        try:
                            capacity = int(capacity)
                            if capacity < 1:
                                raise ValueError("Capacity must be at least 1")
                            new_id = f'classroom_new_{i}'
                            classrooms[new_id] = {
                                'name': name,
                                'capacity': capacity
                            }
                        except ValueError as e:
                            messages.error(request, f"Invalid capacity for new classroom {name}: {str(e)}")
                            return render(request, 'coaching/edit_institution_profile.html', {
                                'form': form,
                                'institution': institution
                            })
                
                # Update the classrooms field
                institution.classrooms = classrooms
                
                # Save all changes in a transaction
                with transaction.atomic():
                    institution.save()
                    messages.success(request, "Institution profile updated successfully!")
                    return redirect('coaching_dashboard', uid=institution.uid)
                    
            except Exception as e:
                logger.error(f"Error updating institution: {str(e)}")
                # Clear any existing messages to prevent mixed messages
                storage = messages.get_messages(request)
                storage.used = True
                messages.error(request, f"An error occurred while updating the institution: {str(e)}")
                return render(request, 'coaching/edit_institution_profile.html', {
                    'form': form,
                    'institution': institution
                })
        else:
            # Clear any existing messages to prevent mixed messages
            storage = messages.get_messages(request)
            storage.used = True
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = InstitutionRegistrationForm(instance=institution)
    
    return render(request, 'coaching/edit_institution_profile.html', {
        'form': form,
        'institution': institution
    })

@login_required
def manage_institution_users(request, uid):
    """Display all students who have joined the institution"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the logged-in user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to view this institution's students.")
        return redirect('coaching_dashboard')
    
    # Get all students who have joined this institution through libraries
    students = CustomUser.objects.filter(
        library__owner=institution.owner,
        library__business_type='Coaching'
    ).distinct()
    
    return render(request, 'coaching/manage_institution_users.html', {
        'institution': institution,
        'students': students
    })

@login_required
def manage_institution_coupons(request, uid):
    """Manage institution coupons"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to manage coupons for this institution.")
        return redirect('coaching_dashboard')
    
    coupons = institution.coupons.all()
    return render(request, 'coaching/manage_institution_coupons.html', {
        'institution': institution,
        'coupons': coupons
    })

@login_required
def create_institution_coupon(request, uid):
    """Create a new institution coupon"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to create coupons for this institution.")
        return redirect('coaching_dashboard')
    
    if request.method == 'POST':
        form = InstitutionCouponForm(request.POST, institution_id=institution.id)
        if form.is_valid():
            try:
                coupon = form.save(commit=False)
                coupon.institution = institution
                coupon.save()
                messages.success(request, "Coupon created successfully!")
                return redirect('manage_institution_coupons', uid=institution.uid)
            except Exception as e:
                logger.error(f"Error creating coupon: {str(e)}")
                messages.error(request, "An error occurred while creating the coupon. Please try again.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = InstitutionCouponForm(institution_id=institution.id)
    
    return render(request, 'coaching/create_institution_coupon.html', {
        'form': form,
        'institution': institution
    })

@login_required
def edit_institution_coupon(request, uid, coupon_id):
    """Edit an existing institution coupon"""
    institution = get_object_or_404(Institution, uid=uid)
    coupon = get_object_or_404(InstitutionCoupon, id=coupon_id, institution=institution)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to edit coupons for this institution.")
        return redirect('coaching_dashboard')
    
    if request.method == 'POST':
        form = InstitutionCouponForm(request.POST, instance=coupon, institution_id=institution.id)
        if form.is_valid():
            try:
                # Save the coupon first
                coupon = form.save(commit=False)
                coupon.institution = institution
                coupon.save()
                
                # Save the many-to-many relationships
                form.save_m2m()
                
                messages.success(request, "Coupon updated successfully!")
                return redirect('manage_institution_coupons', uid=institution.uid)
            except Exception as e:
                logger.error(f"Error updating coupon: {str(e)}")
                messages.error(request, "An error occurred while updating the coupon. Please try again.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = InstitutionCouponForm(instance=coupon, institution_id=institution.id)
    
    return render(request, 'coaching/edit_institution_coupon.html', {
        'form': form,
        'institution': institution,
        'coupon': coupon
    })

@login_required
@require_POST
def delete_institution_coupon(request, uid, coupon_id):
    """Delete an institution coupon"""
    institution = get_object_or_404(Institution, uid=uid)
    coupon = get_object_or_404(InstitutionCoupon, id=coupon_id, institution=institution)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to delete coupons for this institution.")
        return redirect('coaching_dashboard')
    
    try:
        coupon.delete()
        messages.success(request, "Coupon deleted successfully!")
    except Exception as e:
        logger.error(f"Error deleting coupon: {str(e)}")
        messages.error(request, "An error occurred while deleting the coupon. Please try again.")
    
    return redirect('manage_institution_coupons', uid=institution.uid)

@login_required
def institution_reviews(request, uid):
    """Display all reviews for an institution"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to view these reviews.")
        return redirect('coaching_dashboard')
    
    reviews = institution.reviews.all().order_by('-created_at')
    total_reviews = reviews.count()
    average_rating = institution.average_rating()
    
    # Pagination
    paginator = Paginator(reviews, 10)  # Show 10 reviews per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'coaching/institution_reviews.html', {
        'institution': institution,
        'reviews': page_obj,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'page_obj': page_obj
    })

@login_required
@require_POST
def submit_institution_review(request, uid):
    """Submit a review for an institution"""
    institution = get_object_or_404(Institution, uid=uid)
    
    try:
        # Check if user has already reviewed this institution
        existing_review = InstitutionReview.objects.filter(
            institution=institution,
            user=request.user
        ).first()
        
        if existing_review:
            return JsonResponse({
                'status': 'error',
                'message': 'You have already reviewed this institution.'
            }, status=400)
        
        # Create new review
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        
        if not 1 <= rating <= 5:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid rating value.'
            }, status=400)
        
        review = InstitutionReview.objects.create(
            institution=institution,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Review submitted successfully.',
            'review': {
                'user_name': review.user.get_full_name(),
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%B %d, %Y')
            }
        })
        
    except Exception as e:
        logger.error(f"Error submitting review: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while submitting your review.'
        }, status=500)

@login_required
def edit_upi_details(request, uid):
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to edit this institution's UPI details.")
        return redirect('coaching_dashboard', uid=institution.uid)
    
    if request.method == 'POST':
        form = UPIForm(request.POST, instance=institution)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'upi_id': institution.upi_id,
                    'recipient_name': institution.recipient_name,
                    'thank_you_message': institution.thank_you_message
                })
            messages.success(request, "UPI details updated successfully!")
            return redirect('coaching_dashboard', uid=institution.uid)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': ' '.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
                })
            messages.error(request, "Please correct the errors below.")
    else:
        form = UPIForm(instance=institution)
    
    return render(request, 'coaching/edit_upi_details.html', {'form': form, 'institution': institution})

@login_required
@require_POST
def update_institution_image(request, uid):
    """Update institution profile image using Google Drive link."""
    try:
        institution = get_object_or_404(Institution, uid=uid)
        
        # Check if user is the owner
        if request.user != institution.owner:
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to update this institution\'s image.'
            }, status=403)
        
        # Get the Google Drive link
        drive_link = request.POST.get('drive_link')
        if not drive_link:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide a Google Drive link.'
            }, status=400)
        
        # Extract file ID from Google Drive link
        file_id = None
        patterns = [
            r'/file/d/([^/]+)',
            r'/open\?id=([^&]+)',
            r'/uc\?id=([^&]+)',
            r'/uc\?export=view&id=([^&]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, drive_link)
            if match:
                file_id = match.group(1)
                break
        
        if not file_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid Google Drive link format. Please provide a valid link.'
            }, status=400)
        
        # Create new image
        InstitutionImage.objects.create(
            institution=institution,
            google_drive_link=drive_link,
            google_drive_id=file_id
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Image added successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error updating institution image: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while updating the image.'
        }, status=500)

@login_required
@require_POST
def remove_institution_image(request, uid):
    """Remove institution image"""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if the user is the owner of the institution
    if request.user != institution.owner:
        return JsonResponse({
            'status': 'error',
            'message': "You don't have permission to remove this institution's image."
        }, status=403)
    
    try:
        image_id = request.POST.get('image_id')
        if not image_id:
            return JsonResponse({
                'status': 'error',
                'message': 'No image ID provided.'
            }, status=400)
        
        # Get the image and delete it
        image = get_object_or_404(InstitutionImage, id=image_id, institution=institution)
        image.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Image removed successfully.'
        })
        
    except Exception as e:
        logger.error(f"Error removing institution image: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while removing the image.'
        }, status=500)

@login_required
def manage_institution_banner(request, uid):
    """Manage banners for an institution."""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if user has permission to manage banners
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to manage banners for this institution.")
        return redirect('home')
    
    banners = institution.banners.order_by('-created_at')
    
    if request.method == 'POST':
        form = InstitutionBannerForm(request.POST)
        if form.is_valid():
            banner = form.save(commit=False)
            banner.institution = institution
            banner.save()
            messages.success(request, 'Banner added successfully!')
            return redirect('manage_institution_banner', uid=institution.uid)
        else:
            messages.error(request, 'Invalid banner data. Please check the form.')
    else:
        form = InstitutionBannerForm()
    
    context = {
        'institution': institution,
        'banners': banners,
        'form': form,
    }
    
    return render(request, 'coaching/manage_institution_banner.html', context)

@login_required
def delete_institution_banner(request, banner_id):
    """Delete an institution banner."""
    banner = get_object_or_404(InstitutionBanner, id=banner_id)
    institution = banner.institution
    
    # Check if user has permission to delete the banner
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to delete this banner.")
        return redirect('home')
    
    banner.delete()
    messages.success(request, 'Banner deleted successfully!')
    return redirect('manage_institution_banner', uid=institution.uid)

@login_required
def manage_institution_subscriptions(request, uid):
    """Manage subscription plans for an institution."""
    institution = get_object_or_404(Institution, uid=uid)
    
    # Check if user has permission to manage subscriptions
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to manage subscriptions for this institution.")
        return redirect('home')
    
    subscriptions = InstitutionSubscriptionPlan.objects.filter(institution=institution).order_by('-created_at')
    
    if request.method == 'POST':
        form = InstitutionSubscriptionPlanForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.institution = institution
            subscription.save()
            messages.success(request, 'Subscription plan created successfully!')
            return redirect('manage_institution_subscriptions', uid=institution.uid)
        else:
            messages.error(request, 'Invalid subscription data. Please check the form.')
    else:
        form = InstitutionSubscriptionPlanForm()
    
    context = {
        'institution': institution,
        'subscriptions': subscriptions,
        'form': form,
    }
    
    return render(request, 'coaching/manage_institution_subscriptions.html', context)

@login_required
def delete_institution_subscription(request, subscription_id):
    """Delete an institution subscription plan."""
    subscription = get_object_or_404(InstitutionSubscriptionPlan, id=subscription_id)
    institution = subscription.institution
    
    # Check if user has permission to delete the subscription
    if request.user != institution.owner:
        messages.error(request, "You don't have permission to delete this subscription plan.")
        return redirect('home')
    
    subscription.delete()
    messages.success(request, 'Subscription plan deleted successfully!')
    return redirect('manage_institution_subscriptions', uid=institution.uid)

@require_http_methods(["GET"])
def get_subscription(request, subscription_id):
    try:
        subscription = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        # Check if user owns the institution
        if subscription.institution.owner != request.user:
            raise PermissionDenied
        
        data = {
            'id': subscription.id,
            'name': subscription.name,
            'course_duration': subscription.course_duration,
            'start_time': subscription.start_time.strftime('%H:%M'),
            'end_time': subscription.end_time.strftime('%H:%M'),
            'start_date': subscription.start_date.strftime('%Y-%m-%d'),
            'old_price': float(subscription.old_price),
            'new_price': float(subscription.new_price),
            'course_description': subscription.course_description,
            'faculty_description': subscription.faculty_description,
            'subject_cover': subscription.subject_cover,
            'exam_cover': subscription.exam_cover,
        }
        return JsonResponse(data)
    except InstitutionSubscriptionPlan.DoesNotExist:
        return JsonResponse({'error': 'Subscription not found'}, status=404)
    except PermissionDenied:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def update_subscription(request, subscription_id):
    try:
        subscription = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        # Check if user owns the institution
        if subscription.institution.owner != request.user:
            raise PermissionDenied
        
        form = InstitutionSubscriptionPlanForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': form.errors})
    except InstitutionSubscriptionPlan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Subscription not found'}, status=404)
    except PermissionDenied:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def public_institute_subscriptions(request, uid):
    """Public view of institution subscriptions"""
    institution = get_object_or_404(Institution, uid=uid)
    if not institution.is_approved:
        messages.error(request, "This institution is not yet approved.")
        return redirect('home')
    
    subscriptions = InstitutionSubscriptionPlan.objects.filter(
        institution=institution
    ).order_by('-created_at')
    
    return render(request, 'coaching/public_institute_subscriptions.html', {
        'institution': institution,
        'subscriptions': subscriptions,
    })

@require_http_methods(["POST"])
def apply_subscription_coupon(request, subscription_id):
    try:
        # Get subscription and request data
        subscription = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')
        current_price = Decimal(str(data.get('current_price', subscription.old_price)))
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a coupon code'
            })
        
        # Get and validate coupon
        try:
            coupon = InstitutionCoupon.objects.get(
                code=coupon_code,
                institution=subscription.institution,
                status='ACTIVE'
            )
        except InstitutionCoupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid coupon code'
            })
        
        # Check if coupon is valid
        if not coupon.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Coupon has expired or reached maximum usage'
            })
            
        # Check if coupon is applicable to this subscription plan
        if coupon.applicable_plans.exists():
            if subscription not in coupon.applicable_plans.all():
                # Get the list of applicable plans for better error message
                applicable_plans = [plan.name for plan in coupon.applicable_plans.all()]
                return JsonResponse({
                    'success': False,
                    'error': f'This coupon is not applicable to the "{subscription.name}" plan. It can only be used for: {", ".join(applicable_plans)}'
                })
        
        # Calculate discounted price
        try:
            # Convert values to Decimal for precise calculations
            current_price = Decimal(str(current_price))
            discount_value = Decimal(str(coupon.discount_value))
            
            if coupon.discount_type == 'PERCENTAGE':
                # Calculate percentage discount
                discount_amount = (current_price * discount_value) / Decimal('100')
                discounted_price = current_price - discount_amount
            else:  # FIXED amount
                # Apply fixed discount
                discount_amount = discount_value
                discounted_price = current_price - discount_amount
            
            # Ensure discounted price doesn't go below 0
            discounted_price = max(discounted_price, Decimal('0'))
            
            # Calculate savings
            savings = current_price - discounted_price
            
            # Round all values to 2 decimal places
            discounted_price = discounted_price.quantize(Decimal('0.01'))
            savings = savings.quantize(Decimal('0.01'))
            discount_amount = discount_amount.quantize(Decimal('0.01'))
            
            # Store all necessary data in session
            session_key = f'subscription_{subscription_id}'
            request.session[session_key] = {
                'coupon_code': coupon_code,
                'original_price': float(current_price),
                'discount_amount': float(discount_amount),
                'final_price': float(discounted_price),
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'subscription_name': subscription.name,
                'subscription_id': subscription.id,
                'institution_uid': subscription.institution.uid,
                'course_duration': subscription.course_duration,
                'start_time': subscription.start_time.strftime('%H:%M'),
                'end_time': subscription.end_time.strftime('%H:%M'),
                'start_date': subscription.start_date.strftime('%Y-%m-%d')
            }
            
            
            return JsonResponse({
                'success': True,
                'message': 'Coupon applied successfully',
                'discounted_price': str(discounted_price),
                'discount_amount': str(discount_amount),
                'original_price': str(current_price),
                'coupon_code': coupon_code,
                'applicable_plans': [plan.name for plan in coupon.applicable_plans.all()] if coupon.applicable_plans.exists() else ['All Plans'],
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value)
            })
            
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            logger.error(f"Error calculating discount: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error calculating discount. Please try again.'
            })
            
    except InstitutionSubscriptionPlan.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Subscription plan not found'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data'
        })
    except Exception as e:
        logger.error(f"Unexpected error in apply_subscription_coupon: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        })

@login_required
def institute_subscription_payment(request, uid, subscription_id):
    try:
        institution = Institution.objects.get(uid=uid)
        subscription_plan = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        
        # Get stored session data
        session_key = f'subscription_{subscription_id}'
        session_data = request.session.get(session_key, {})
        
        if not session_data:
            # If no session data exists, use default values
            current_price = subscription_plan.new_price
            applied_coupon = None
            discount_amount = 0
            original_price = subscription_plan.old_price
        else:
            # Use stored session data
            current_price = Decimal(str(session_data.get('final_price', subscription_plan.new_price)))
            applied_coupon = session_data.get('coupon_code')
            discount_amount = Decimal(str(session_data.get('discount_amount', 0)))
            original_price = Decimal(str(session_data.get('original_price', subscription_plan.old_price)))
        
        # Generate UPI payment URL
        upi_url = f"upi://pay?pa={institution.upi_id}&pn={institution.recipient_name}&am={float(current_price)}&cu=INR&tn=Subscription Payment"
        
        # Generate QR code for UPI payment
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert QR code to base64 for display
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        context = {
            'institution': institution,
            'subscription_plan': subscription_plan,
            'current_price': current_price,
            'applied_coupon': applied_coupon,
            'upi_url': upi_url,
            'qr_code': qr_image_base64,
            'upi_id': institution.upi_id,
            'recipient_name': institution.recipient_name,
            'original_price': original_price,
            'discount_amount': discount_amount,
            'final_price': current_price,
        }
        
        return render(request, 'coaching/institute_subscription_payment.html', context)
        
    except Institution.DoesNotExist:
        messages.error(request, 'Institution not found.')
        return redirect('home')
    except InstitutionSubscriptionPlan.DoesNotExist:
        messages.error(request, 'Subscription plan not found.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in institute_subscription_payment: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('home')

@login_required
def process_subscription_payment(request, institution_id, subscription_id):
    try:
        institution = Institution.objects.get(id=institution_id)
        subscription = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        
        # Get the final price and coupon from session
        session_price = request.session.get(f'subscription_{subscription_id}_price')
        coupon_code = request.session.get(f'subscription_{subscription_id}_coupon')
        
        # Get the current price
        current_price = Decimal(str(session_price)) if session_price is not None else subscription.new_price
        
        # Get the applied coupon if any
        applied_coupon = None
        if coupon_code:
            try:
                applied_coupon = InstitutionCoupon.objects.get(
                    code=coupon_code,
                    institution=institution,
                    status='ACTIVE'
                )
                if not applied_coupon.is_valid():
                    applied_coupon = None
            except InstitutionCoupon.DoesNotExist:
                applied_coupon = None
        
        # Calculate the final price
        if applied_coupon:
            if applied_coupon.discount_type == 'PERCENTAGE':
                discount_amount = (current_price * applied_coupon.discount_value) / Decimal('100')
            else:  # FIXED
                discount_amount = applied_coupon.discount_value
            current_price = max(current_price - discount_amount, Decimal('0'))
            current_price = current_price.quantize(Decimal('0.01'))
        
        # Get transaction ID from form
        transaction_id = request.POST.get('transaction_id')
        if not transaction_id:
            messages.error(request, 'Transaction ID is required')
            return redirect('institute_subscription_payment', uid=institution.uid, subscription_id=subscription_id)
        
        # Create the subscription
        subscription = InstitutionSubscription.objects.create(
            user=request.user,
            subscription_plan=subscription,
            start_date=subscription.start_date,
            end_date=subscription.start_date + timedelta(days=30 * subscription.course_duration),
            start_time=subscription.start_time,
            end_time=subscription.end_time,
            amount_paid=current_price,
            transaction_id=transaction_id,
            coupon_applied=applied_coupon
        )
        
        # Use the coupon if it was applied
        if applied_coupon:
            applied_coupon.use_coupon()
        
        # Clear session data
        request.session.pop(f'subscription_{subscription_id}_price', None)
        request.session.pop(f'subscription_{subscription_id}_coupon', None)
        
        messages.success(request, 'Subscription purchased successfully!')
        return redirect('institute_subscription_details', uid=institution.uid, subscription_id=subscription.id)
        
    except Institution.DoesNotExist:
        messages.error(request, 'Institution not found')
        return redirect('home')
    except InstitutionSubscriptionPlan.DoesNotExist:
        messages.error(request, 'Subscription plan not found')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in process_subscription_payment: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment')
        return redirect('institute_subscription_payment', uid=institution.uid, subscription_id=subscription_id)

@login_required
def institute_subscription_details(request, uid, subscription_id):
    try:
        institution = Institution.objects.get(uid=uid)
        subscription = InstitutionSubscription.objects.get(
            id=subscription_id,
            user=request.user,
            subscription_plan__institution=institution
        )
        
        context = {
            'institution': institution,
            'subscription': subscription,
            'subscription_plan': subscription.subscription_plan,
            'has_coupon': subscription.coupon_applied is not None,
            'coupon': subscription.coupon_applied,
            'original_price': subscription.subscription_plan.old_price,
            'discount_amount': subscription.subscription_plan.old_price - subscription.amount_paid if subscription.coupon_applied else 0,
            'final_price': subscription.amount_paid
        }
        
        return render(request, 'coaching/institute_subscription_details.html', context)
        
    except Institution.DoesNotExist:
        messages.error(request, 'Institution not found')
        return redirect('home')
    except InstitutionSubscription.DoesNotExist:
        messages.error(request, 'Subscription not found')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in institute_subscription_details: {str(e)}")
        messages.error(request, 'An error occurred while loading subscription details')
        return redirect('home')