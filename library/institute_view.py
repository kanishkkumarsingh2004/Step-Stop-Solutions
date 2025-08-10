# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from .forms import InstitutionRegistrationForm, InstitutionCouponForm, UPIForm, InstitutionBannerForm, InstitutionSubscriptionPlanForm
from django.contrib import messages
from .models import (Institution, 
                    CustomUser, 
                    InstitutionCoupon, 
                    InstitutionReview, 
                    InstitutionImage, 
                    InstitutionBanner, 
                    InstitutionSubscriptionPlan, 
                    InstitutionSubscription, 
                    PaymentVerification, 
                    InstitutionExpense, 
                    TimetableEntry, 
                    Institution, 
                    SubjectFacultyMap, 
                    AdminCard, 
                    InstitutionCardLog, 
                    InstitutionStaff, 
                    CoachingAttendance)
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
from datetime import timedelta, datetime
import qrcode
from collections import defaultdict

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
        
        
        context = {
            'institution': institution,
            'active_coupons_count': active_coupons_count,
            'total_coupons_count': total_coupons_count,
            'expired_coupons_count': expired_coupons_count,
            'primary_image': first_image,  # Keep the variable name for template compatibility

        }
        
        return render(request, 'coaching/coaching_dashboard.html', context)
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
    
    has_active_subscription = False
    if request.user.is_authenticated:
        has_active_subscription = InstitutionSubscription.objects.filter(
            user=request.user,
        ).exists()
        
    return render(request, 'coaching/public_institute_details.html', {
        'institution': institution,
        'images': images,
        'has_timetable': TimetableEntry.objects.filter(institution=institution).exists(),
        'has_active_subscription': has_active_subscription
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
    """Display all students who have enrolled in the institution through subscriptions"""
    institution = get_object_or_404(Institution, uid=uid)

    # Get all students who have subscribed to this institution's subscription plans
    subscriptions = InstitutionSubscription.objects.filter(
        subscription_plan__institution=institution
    ).select_related('user', 'subscription_plan').order_by('-created_at')
    
    # Get unique users with their subscription details
    enrolled_users = []
    seen_users = set()
    
    for subscription in subscriptions:
        user_id = subscription.user.id
        if user_id not in seen_users:
            seen_users.add(user_id)
            enrolled_users.append({
                'user': subscription.user,
                'subscription': subscription,
                'subscription_plan': subscription.subscription_plan,
                'enrollment_date': subscription.created_at,
                'payment_status': subscription.payment_status,
                'payment_method': subscription.payment_method,
                'amount_paid': subscription.amount_paid
            })
    
    return render(request, 'coaching/manage_institution_users.html', {
        'institution': institution,
        'enrolled_users': enrolled_users,
        'total_enrolled': len(enrolled_users)
    })

@login_required
def manage_institution_coupons(request, uid):
    """Manage institution coupons"""
    institution = get_object_or_404(Institution, uid=uid)
    

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
            
        # Check if user has already used this coupon
        if coupon.has_been_used_by_user(request.user):
            return JsonResponse({
                'success': False,
                'error': 'You have already used this coupon'
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
        
        # Get coupon data from session buffer
        session_key = f'subscription_{subscription_id}'
        session_data = request.session.get(session_key, {})

        # Check if we have valid coupon data in session
        has_coupon = False
        if session_data and isinstance(session_data, dict):
            try:
                # Verify the coupon still exists and is valid
                coupon = InstitutionCoupon.objects.get(
                    code=session_data.get('coupon_code'),
                    institution=institution,
                    status='ACTIVE'
                )
                
                if coupon.is_valid():
                    has_coupon = True
                    current_price = Decimal(str(session_data.get('final_price', subscription_plan.new_price)))
                    applied_coupon = session_data.get('coupon_code')
                    discount_amount = Decimal(str(session_data.get('discount_amount', 0)))
                    original_price = Decimal(str(session_data.get('original_price', subscription_plan.old_price)))
                    
                    logger.info(f"Using coupon data from session: {session_data}")
                else:
                    logger.warning(f"Coupon {session_data.get('coupon_code')} is not valid")
                    has_coupon = False
            except InstitutionCoupon.DoesNotExist:
                logger.warning(f"Coupon {session_data.get('coupon_code')} not found")
                has_coupon = False
            except Exception as e:
                logger.error(f"Error processing coupon from session: {str(e)}")
                has_coupon = False
        
        if not has_coupon:
            # Use default subscription prices
            current_price = subscription_plan.new_price
            applied_coupon = None
            discount_amount = Decimal('0')
            original_price = subscription_plan.old_price
        # Generate a timestamp for the transaction reference
        import time
        timestamp = int(time.time())
        tr = f"{timestamp}"
        # Generate UPI payment URL with the correct price and timestamp as 'tr'
        upi_url = f"upi://pay?pa={institution.upi_id}&pn={institution.recipient_name}&am={float(current_price)}&cu=INR&tn=Subscription Payment&tr={tr}"
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
            'has_coupon': has_coupon,
        }
        
        # Clear the session data after processing
        request.session.pop(session_key, None)
        
        logger.info(f"Rendering payment page with context: {context}")
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
def process_subscription_payment(request, uid, subscription_id):
    try:
        institution = Institution.objects.get(uid=uid)
        subscription_plan = InstitutionSubscriptionPlan.objects.get(id=subscription_id)
        
        # Get the final price and coupon from form
        final_price = Decimal(request.POST.get('final_price', subscription_plan.new_price))
        final_coupon = request.POST.get('final_coupon')
        payment_method = request.POST.get('payment_method', 'cash')
        
        # Get the applied coupon if any
        applied_coupon = None
        if final_coupon:
            try:
                applied_coupon = InstitutionCoupon.objects.get(
                    code=final_coupon,
                    institution=institution,
                    status='ACTIVE'
                )
                if not applied_coupon.is_valid() or applied_coupon.has_been_used_by_user(request.user):
                    applied_coupon = None
            except InstitutionCoupon.DoesNotExist:
                applied_coupon = None
        
        # Get transaction ID from form
        transaction_id = request.POST.get('transaction_id', '').strip()
        
        # Validate transaction ID based on payment method
        if payment_method == 'upi' and not transaction_id:
            messages.error(request, 'Transaction ID is required for UPI payments')
            return redirect('institute_subscription_payment', uid=institution.uid, subscription_id=subscription_id)
        
        # For cash payments, generate a reference if no transaction ID provided
        if payment_method == 'cash' and not transaction_id:
            transaction_id = f"CASH_{request.user.id}_{int(timezone.now().timestamp())}"
        
        # Create the subscription
        subscription = InstitutionSubscription.objects.create(
            user=request.user,
            subscription_plan=subscription_plan,
            start_date=subscription_plan.start_date,
            end_date=subscription_plan.start_date + timedelta(days=30 * subscription_plan.course_duration),
            start_time=subscription_plan.start_time,
            end_time=subscription_plan.end_time,
            amount_paid=final_price,
            transaction_id=transaction_id,
            payment_method=payment_method,
            coupon_applied=applied_coupon,
            status='Valid'  # Set initial status as pending
        )
        
        # Use the coupon if it was applied
        if applied_coupon:
            applied_coupon.use_coupon(request.user)
        
        # Calculate discount amount for the success page
        discount_amount = subscription_plan.old_price - final_price if applied_coupon else 0
        
        # Render success page
        return render(request, 'coaching/subscription_payment_success.html', {
            'subscription': subscription,
            'institution': institution,
            'subscription_plan': subscription_plan,
            'discount_amount': discount_amount,
            'original_price': subscription_plan.old_price,
            'final_price': final_price,
            'applied_coupon': applied_coupon.code if applied_coupon else None,
            'transaction_id': transaction_id,
            'payment_method': payment_method
        })
        
    except Institution.DoesNotExist:
        messages.error(request, 'Institution not found')
        return redirect('home')
    except InstitutionSubscriptionPlan.DoesNotExist:
        messages.error(request, 'Subscription plan not found')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in process_subscription_payment: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment')
        return redirect('institute_subscription_payment', uid=uid, subscription_id=subscription_id)

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

@login_required
def verify_payment(request, uid, subscription_id):
    try:
        institution = Institution.objects.get(uid=uid)
        subscription = InstitutionSubscription.objects.get(id=subscription_id, subscription_plan__institution=institution)
        
        if request.method == 'POST':
            status = request.POST.get('status')
            
            if status in ['pending', 'valid', 'invalid']:
                # Create or update verification record
                verification, created = PaymentVerification.objects.get_or_create(
                    subscription=subscription,
                    defaults={
                        'status': 'verified' if status == 'valid' else 'rejected' if status == 'invalid' else 'pending',
                        'verified_by': request.user if status != 'pending' else None,
                        'verification_notes': f'Status changed to {status}'
                    }
                )
                
                if not created:
                    verification.status = 'verified' if status == 'valid' else 'rejected' if status == 'invalid' else 'pending'
                    verification.verified_by = request.user if status != 'pending' else None
                    verification.verification_notes = f'Status changed to {status}'
                    verification.save()
                
                # Update subscription payment status
                subscription.payment_status = status
                subscription.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Payment status updated to {status}'
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid status value'
            }, status=400)
            
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)
        
    except Institution.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Institution not found'
        }, status=404)
    except InstitutionSubscription.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Subscription not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in verify_payment: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while verifying payment'
        }, status=500)

@login_required
def payment_verifications(request, uid):
    try:
        institution = Institution.objects.get(uid=uid)
        
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        search_query = request.GET.get('search', '').strip()
        
        # Base queryset
        subscriptions = InstitutionSubscription.objects.filter(
            subscription_plan__institution=institution
        ).select_related('user', 'subscription_plan')
        
        # Apply status filter
        if status_filter != 'all':
            subscriptions = subscriptions.filter(payment_status=status_filter)
        
        # Apply search filter
        if search_query:
            subscriptions = subscriptions.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(transaction_id__icontains=search_query) |
                Q(subscription_plan__name__icontains=search_query)
            )
        
        # Get verifications for the filtered subscriptions
        verifications = PaymentVerification.objects.filter(
            subscription__in=subscriptions
        ).select_related('verified_by', 'subscription__user', 'subscription__subscription_plan')
        
        context = {
            'institution': institution,
            'subscriptions': subscriptions,
            'verifications': verifications,
            'current_status': status_filter,
            'search_query': search_query
        }
        
        return render(request, 'coaching/payment_verifications.html', context)
        
    except Institution.DoesNotExist:
        messages.error(request, 'Institution not found')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in payment_verifications: {str(e)}")
        messages.error(request, 'An error occurred while loading payment verifications')
        return redirect('home')

@login_required
def payment_expenses(request, uid):
    try:
        institution = Institution.objects.get(uid=uid)
        # Check if the current user is the owner of the institution
        if request.user != institution.owner:
            messages.error(request, "You don't have permission to view this page.")
            return redirect('home')
        
        # Get filter parameters
        transaction_type = request.GET.get('type', 'all')
        search_query = request.GET.get('search', '')
        
        # Get all subscriptions (income)
        subscriptions = InstitutionSubscription.objects.filter(
            subscription_plan__institution=institution
        )
        
        # Get all expenses with complete data
        expenses = InstitutionExpense.objects.filter(institution=institution).select_related('institution')
        
        # Apply search filter if provided
        if search_query:
            subscriptions = subscriptions.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(subscription_plan__name__icontains=search_query)
            )
            expenses = expenses.filter(
                Q(description__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(expense_type__icontains=search_query) |
                Q(payment_mode__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
        
        # Calculate totals
        total_income = subscriptions.filter(payment_status='valid').aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        total_expenses = expenses.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        net_balance = total_income - total_expenses
        
        # Prepare transactions list with complete data
        transactions = []
        
        # Add income transactions
        for sub in subscriptions:
            transactions.append({
                'date': sub.created_at.date(),
                'description': f"Payment from {sub.user.get_full_name()} - {sub.subscription_plan.name}",
                'type': 'income',
                'amount': sub.amount_paid,
                'payment_mode': sub.payment_method,
                'transaction_id': sub.transaction_id,
                'notes': f"Transaction ID: {sub.transaction_id}"
            })
        
        # Add expense transactions with all fields
        for expense in expenses:
            transactions.append({
                'date': expense.date,
                'description': expense.description,
                'type': 'expense',
                'amount': expense.amount,
                'payment_mode': expense.payment_mode,
                'transaction_id': expense.transaction_id,
                'notes': expense.notes,
                'expense_type': expense.get_expense_type_display(),
                'created_at': expense.created_at
            })
        
        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Filter transactions by type if specified
        if transaction_type != 'all':
            transactions = [t for t in transactions if t['type'] == transaction_type]

        context = {
            'institution': institution,
            'transactions': transactions,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'transaction_type': transaction_type,
            'search_query': search_query,
            'expense_types': dict(InstitutionExpense.EXPENSE_TYPES),
            'payment_modes': dict(InstitutionExpense.PAYMENT_MODES)
        }
        
        return render(request, 'coaching/payment_expenses.html', context)
        
    except Institution.DoesNotExist:
        messages.error(request, "Institution not found.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in payment_expenses: {str(e)}")
        messages.error(request, "An error occurred while loading the page.")
        return redirect('home')

@login_required
@require_http_methods(["POST"])
def add_institution_expense(request, uid):
    try:
        institution = Institution.objects.get(uid=uid)
        
        # Check if the current user is the owner of the institution
        if request.user != institution.owner:
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to add expenses for this institution."
            }, status=403)
        
        # Parse JSON data from request
        try:
            data = json.loads(request.body)
            logger.info(f"Received expense data: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request data format.'
            }, status=400)
        
        # Validate required fields
        required_fields = ['expense_type', 'description', 'amount', 'date', 'payment_mode']
        for field in required_fields:
            if not data.get(field):
                logger.error(f"Missing required field: {field}")
                return JsonResponse({
                    'status': 'error',
                    'message': f"{field.replace('_', ' ').title()} is required."
                }, status=400)
        
        # Validate payment mode and transaction ID
        if data['payment_mode'] in ['card', 'upi'] and not data.get('transaction_id'):
            logger.error("Transaction ID missing for card/upi payment")
            return JsonResponse({
                'status': 'error',
                'message': 'Transaction ID is required for Card/UPI payments.'
            }, status=400)
        
        try:
            # Parse the date string to a date object
            from datetime import datetime
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Create the expense
            expense = InstitutionExpense.objects.create(
                institution=institution,
                expense_type=data['expense_type'],
                description=data['description'],
                amount=data['amount'],
                date=date_obj,
                payment_mode=data['payment_mode'],
                transaction_id=data.get('transaction_id'),
                notes=data.get('notes')
            )
            
            logger.info(f"Successfully created expense with ID: {expense.id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Expense added successfully!',
                'expense': {
                    'id': expense.id,
                    'description': expense.description,
                    'amount': str(expense.amount),
                    'date': expense.date.isoformat(),
                    'notes': expense.notes
                }
            })
            
        except ValueError as e:
            logger.error(f"Date parsing error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid date format. Please use YYYY-MM-DD format.'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error creating expense: {str(e)}'
            }, status=500)
        
    except Institution.DoesNotExist:
        logger.error(f"Institution not found with uid: {uid}")
        return JsonResponse({
            'status': 'error',
            'message': 'Institution not found.'
        }, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in add_institution_expense: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)

@login_required
def expense_analytics(request, uid):
    try:
        institution = Institution.objects.get(uid=uid)
    
        
        # Get all valid subscriptions and expenses
        subscriptions = InstitutionSubscription.objects.filter(
            subscription_plan__institution=institution,
            payment_status='valid'  # Add payment_status filter
        )
        expenses = InstitutionExpense.objects.filter(institution=institution)
        
        # Calculate totals
        total_income = subscriptions.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        net_balance = total_income - total_expenses
        
        # Prepare data for Income vs Expenses Line Chart
        dates = []
        income_data = []
        expense_data = []
        cumulative_income = 0
        cumulative_expense = 0
        
        # Get all unique dates from both subscriptions and expenses
        all_dates = set()
        for sub in subscriptions:
            payment_date = sub.created_at.date()
            all_dates.add(payment_date)
        
        for exp in expenses:
            all_dates.add(exp.date)
        
        # Sort dates
        sorted_dates = sorted(list(all_dates))
        
        # Prepare data for each date
        for date in sorted_dates:
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Calculate daily income
            daily_income = subscriptions.filter(
                created_at__date=date,
                payment_status='valid'  # Add payment_status filter
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Calculate daily expenses
            daily_expenses = expenses.filter(date=date).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate cumulative totals
            cumulative_income += float(daily_income)
            cumulative_expense += float(daily_expenses)
            
            income_data.append(cumulative_income)
            expense_data.append(cumulative_expense)
        
        # Prepare data for Expense Types Pie Chart
        expense_types = []
        expense_type_data = []
        for expense_type, _ in InstitutionExpense.EXPENSE_TYPES:
            total = expenses.filter(expense_type=expense_type).aggregate(total=Sum('amount'))['total'] or 0
            if total > 0:
                expense_types.append(expense_type)
                expense_type_data.append(float(total))
        
        # Prepare data for Payment Methods Bar Chart
        payment_methods = []
        payment_method_data = []
        
        # Get payment methods from expenses
        for payment_mode, _ in InstitutionExpense.PAYMENT_MODES:
            total = expenses.filter(payment_mode=payment_mode).aggregate(total=Sum('amount'))['total'] or 0
            if total > 0:
                payment_methods.append(payment_mode)
                payment_method_data.append(float(total))
        
        # Get payment methods from subscriptions (income)
        for payment_method, _ in InstitutionSubscription.PAYMENT_METHOD_CHOICES:
            total = subscriptions.filter(payment_method=payment_method).aggregate(total=Sum('amount_paid'))['total'] or 0
            if total > 0:
                if payment_method not in payment_methods:
                    payment_methods.append(payment_method)
                    payment_method_data.append(float(total))
                else:
                    # Add to existing payment method total
                    idx = payment_methods.index(payment_method)
                    payment_method_data[idx] += float(total)
        
        # Prepare data for Monthly Trend Chart
        from datetime import datetime, timedelta
        
        monthly_labels = []
        monthly_income = []
        monthly_expenses = []
        
        # Get last 6 months
        today = timezone.now().date()
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            monthly_labels.append(month_start.strftime('%b %Y'))
            month_income = subscriptions.filter(
                created_at__date__gte=month_start,
                created_at__date__lte=month_end,
                payment_status='valid'  # Add payment_status filter
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            month_expenses = expenses.filter(
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_income.append(float(month_income))
            monthly_expenses.append(float(month_expenses))
        
        # Prepare data for Expense Categories Bar Chart
        expense_categories = []
        expense_amounts = []
        for expense_type, display_name in InstitutionExpense.EXPENSE_TYPES:
            total = expenses.filter(expense_type=expense_type).aggregate(total=Sum('amount'))['total'] or 0
            if total > 0:
                expense_categories.append(display_name)  # Use display name instead of internal value
                expense_amounts.append(float(total))
        
        context = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'dates': json.dumps(dates),
            'income_data': json.dumps(income_data),
            'expense_data': json.dumps(expense_data),
            'expense_types': json.dumps(expense_types),
            'expense_type_data': json.dumps(expense_type_data),
            'payment_methods': json.dumps(payment_methods),
            'payment_method_data': json.dumps(payment_method_data),
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_income': json.dumps(monthly_income),
            'monthly_expenses': json.dumps(monthly_expenses),
            'expense_categories': json.dumps(expense_categories),
            'expense_amounts': json.dumps(expense_amounts),
        }
        
        return render(request, 'coaching/expense_analytics.html', context)
    except Institution.DoesNotExist:
        messages.error(request, "Institution not found.")
        return redirect('home')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')
        

@csrf_exempt
def save_timetable(request, institution_uid):
    if request.method == "POST":
        data = json.loads(request.body)
        entries = data.get("entries", [])
        institution = Institution.objects.get(uid=institution_uid)
        updated = 0
        created = 0

        for entry in entries:
            obj, created_flag = TimetableEntry.objects.update_or_create(
                institution=institution,
                day=entry["day"],
                classroom=entry["classroom"],
                cell_row=entry["cell_row"],
                cell_col=entry["cell_col"],
                defaults={
                    "start_time": entry["start_time"],
                    "end_time": entry["end_time"],
                    "subject": entry["subject"],
                    "faculty_ssid": entry["faculty_ssid"],
                    "faculty_name": entry["faculty_name"],
                }
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        return JsonResponse({"status": "success", "updated": updated, "created": created})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)



@csrf_exempt
@require_POST
def save_subject_faculty(request, institution_uid):
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        faculty_ssid = data.get('faculty_ssid')
        faculty_name = data.get('faculty_name', '')

        if not subject or not faculty_ssid:
            return JsonResponse({'status': 'error', 'message': 'Subject and faculty_ssid are required.'}, status=400)

        institution = Institution.objects.get(uid=institution_uid)
        obj, created = SubjectFacultyMap.objects.update_or_create(
            institution=institution,
            subject=subject,
            defaults={
                'faculty_ssid': faculty_ssid,
                'faculty_name': faculty_name
            }
        )
        return JsonResponse({'status': 'success', 'created': created})
    except Institution.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Institution not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
from django.views.decorators.http import require_GET

@require_GET
def get_faculty_name_by_ssid(request):
    ssid = request.GET.get('ssid')
    if not ssid:
        return JsonResponse({'status': 'error', 'message': 'SSID is required.'})
    try:
        user = CustomUser.objects.get(ssid=ssid)
        return JsonResponse({'status': 'success', 'faculty_name': user.get_full_name()})
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Faculty not found.'})

@csrf_exempt
@require_POST
def remove_subject(request, institution_uid):
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        if not subject:
            return JsonResponse({'status': 'error', 'message': 'Subject is required.'}, status=400)
        institution = Institution.objects.get(uid=institution_uid)
        deleted, _ = SubjectFacultyMap.objects.filter(institution=institution, subject=subject).delete()
        if deleted:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Subject not found.'}, status=404)
    except Institution.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Institution not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def view_schedule(request, uid):
    institution = get_object_or_404(Institution, uid=uid)
    if not institution.is_approved:
        messages.error(request, "This institution is not yet approved.")
        return redirect('home')

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
    
    sorted_scheduled_classrooms = {}
    for day, classrooms in scheduled_classrooms.items():
        sorted_scheduled_classrooms[day] = sorted(list(classrooms))

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return render(request, 'coaching/view_schedule.html', {
        'institution': institution,
        'timetable_map': timetable_map,
        'header_time_map': header_time_map,
        'day_col_indices': day_col_indices,
        'day_classrooms': sorted_scheduled_classrooms,
        'days_of_week': days_of_week
    })

@login_required
def allocate_card_to_institution_page(request, uid):
    institution = get_object_or_404(Institution, uid=uid)

    # Get all users who have ever subscribed to this institution
    enrolled_user_ids = InstitutionSubscription.objects.filter(
        subscription_plan__institution=institution
    ).values_list('user_id', flat=True).distinct()

    # Get users without card by checking InstitutionCardLog
    users_with_card = InstitutionCardLog.objects.filter(
        institution=institution
    ).values_list('user_id', flat=True).distinct()

    # Get enrolled users who don't have a card assigned
    users_without_card = CustomUser.objects.filter(
        id__in=enrolled_user_ids
    ).exclude(
        id__in=users_with_card
    )

    # Augment user data with subscription status
    users_with_status = []
    for user in users_without_card:
        has_active_subscription = InstitutionSubscription.objects.filter(
            user=user,
            subscription_plan__institution=institution,
            status='valid',
            payment_status='valid'
        ).exists()
        
        users_with_status.append({
            'user': user,
            'has_active_subscription': has_active_subscription
        })

    context = {
        'institution': institution,
        'users_with_status': users_with_status
    }
    return render(request, 'coaching/allocate_card_to_institution.html', context)


@login_required
@require_POST
def allocate_card_to_institution(request):
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        user_id = data.get('user_id')
        institution_uid = data.get('institution_uid')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid request format.'}, status=400)

    if not all([card_id, user_id, institution_uid]):
        return JsonResponse({'status': 'error', 'message': 'Card ID, User, and Institution are required.'}, status=400)

    institution = get_object_or_404(Institution, uid=institution_uid)
    user_to_allocate = get_object_or_404(CustomUser, id=user_id)

    # Check permission
    if request.user != institution.owner:
        return JsonResponse({'status': 'error', 'message': "You don't have permission to perform this action."}, status=403)

    # Check if user already has a card
    if user_to_allocate.nfc_id:
        return JsonResponse({'status': 'error', 'message': f"User {user_to_allocate.get_full_name()} already has a card."}, status=400)

    # Check if the card is available in AdminCard
    try:
        admin_card = AdminCard.objects.get(card_id=card_id)
        if admin_card.library or admin_card.institution:
            return JsonResponse({'status': 'error', 'message': "This card is already allocated."}, status=400)
    except AdminCard.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': "This card is not registered in the system."}, status=400)
        
    # Check for subscription one more time
    has_subscription = InstitutionSubscription.objects.filter(
        user=user_to_allocate,
        subscription_plan__institution=institution,
        status='valid',
        payment_status='valid'
    ).exists()

    if not has_subscription:
        return JsonResponse({'status': 'error', 'message': f"User {user_to_allocate.get_full_name()} does not have a valid subscription."}, status=400)
    
    # Allocate card
    try:
        with transaction.atomic():
            user_to_allocate.nfc_id = card_id
            user_to_allocate.save()

            admin_card.institution = institution
            admin_card.save()

            # Create a log entry for the allocation
            InstitutionCardLog.objects.create(
                institution=institution,
                user=user_to_allocate,
                card_id=card_id,
                allocated_by=request.user
            )
            
            return JsonResponse({'status': 'success', 'message': f"Card {card_id} allocated to {user_to_allocate.get_full_name()} successfully."})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"}, status=500)

@login_required
def manage_institution_staff(request, uid):
    """Manage staff for an institution."""
    institution = get_object_or_404(Institution, uid=uid)   

    staff_list = InstitutionStaff.objects.filter(institution=institution)
    permission_choices = InstitutionStaff.PERMISSION_CHOICES

    # Check if the owner is also a staff member
    is_staff_member = InstitutionStaff.objects.filter(institution=institution, user=request.user).exists()

    context = {
        'institution': institution,
        'staff_list': staff_list,
        'permission_choices': permission_choices,
        'is_staff_member': is_staff_member,
    }
    return render(request, 'coaching/manage_institution_staff.html', context)


@login_required
@require_POST
def add_institution_staff(request, uid):
    institution = get_object_or_404(Institution, uid=uid)
    if request.user != institution.owner:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user = CustomUser.objects.get(id=user_id)

        if InstitutionStaff.objects.filter(institution=institution, user=user).exists():
            return JsonResponse({'status': 'error', 'message': 'This user is already a staff member.'}, status=400)

        staff = InstitutionStaff.objects.create(institution=institution, user=user)
        return JsonResponse({
            'status': 'success',
            'message': 'Staff added successfully.',
            'staff': {
                'id': staff.id,
                'full_name': user.get_full_name(),
                'email': user.email,
                'permissions': []
            }
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def update_institution_staff_permissions(request, staff_id):
    staff = get_object_or_404(InstitutionStaff, id=staff_id)
    institution = staff.institution
    if request.user != institution.owner:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    try:
        data = json.loads(request.body)
        permissions = data.get('permissions', [])
        staff.permissions = ",".join(permissions)
        staff.save()
        return JsonResponse({'status': 'success', 'message': 'Permissions updated successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def remove_institution_staff(request, staff_id):
    staff = get_object_or_404(InstitutionStaff, id=staff_id)
    institution = staff.institution
    if request.user != institution.owner:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    try:
        staff.delete()
        return JsonResponse({'status': 'success', 'message': 'Staff member removed successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def institution_staff_dashboard(request, uid):
    """Display the staff dashboard for an institution."""
    institution = get_object_or_404(Institution, uid=uid)

    try:
        staff_member = InstitutionStaff.objects.get(institution=institution, user=request.user)
        permissions = staff_member.get_permissions()
    except InstitutionStaff.DoesNotExist:
        messages.error(request, "You are not registered as a staff member for this institution.")
        return redirect('home')

    # Schedule context (copied from view_schedule)
    timetable_entries = list(TimetableEntry.objects.filter(institution=institution).values())
    timetable_map = {}
    for entry in timetable_entries:
        key = (entry['day'], entry['classroom'], entry['cell_col'])
        timetable_map[key] = entry
    header_time_map = {}
    for entry in timetable_entries:
        key = (entry['day'], entry['cell_col'])
        if key not in header_time_map:
            header_time_map[key] = entry
    from collections import defaultdict
    max_cols = defaultdict(int)
    for entry in timetable_entries:
        day = entry['day']
        col = entry.get('cell_col', 0)
        if col + 1 > max_cols[day]:
            max_cols[day] = col + 1
    day_col_indices = {day: list(range(max_col)) for day, max_col in max_cols.items()}
    scheduled_classrooms = defaultdict(set)
    for entry in timetable_entries:
        if entry['classroom']:
            scheduled_classrooms[entry['day']].add(entry['classroom'])
    sorted_scheduled_classrooms = {}
    for day, classrooms in scheduled_classrooms.items():
        sorted_scheduled_classrooms[day] = sorted(list(classrooms))
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    context = {
        'institution': institution,
        'permissions': permissions,
        'days_of_week': days_of_week,
        'timetable_map': timetable_map,
        'header_time_map': header_time_map,
        'day_col_indices': day_col_indices,
        'day_classrooms': sorted_scheduled_classrooms,
    }

    return render(request, 'coaching/institution_staff_dashboard.html', context)

@login_required
def manage_institution_cards(request):
    # Only get cards that are allocated to an institution
    allocated_cards = AdminCard.objects.filter(institution__isnull=False).select_related('institution')
    
    search_query = request.GET.get('search')
    if search_query:
        allocated_cards = allocated_cards.filter(
            Q(card_id__icontains=search_query) |
            Q(institution__name__icontains=search_query)
        )
    
    paginator = Paginator(allocated_cards, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'allocated_cards': page_obj,
    }
    return render(request, 'coaching/manage_institution_cards.html', context)

@login_required
def coaching_attendance_page(request, uid):
    institute = get_object_or_404(Institution, uid=uid)
    return render(request, 'coaching/coaching_attendance_page.html', {'library': institute})

@csrf_exempt
def mark_institute_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nfc_serial = data.get("nfc_serial")
            institute_id = data.get("institute_id") or data.get("institution_id") or data.get("library_id")

            if not nfc_serial or not institute_id:
                return JsonResponse({"error": "NFC serial and Institution ID are required"}, status=400)

            # Use InstitutionCardLog to look up the user by card_id (NFC serial) and institution
            card_log = InstitutionCardLog.objects.filter(
                card_id=nfc_serial,
                institution__uid=institute_id
            ).order_by('-timestamp').first()
            if not card_log or not card_log.user:
                return JsonResponse({"error": "User not found for this NFC serial"}, status=404)
            user = card_log.user

            try:
                institution = Institution.objects.get(uid=institute_id)
            except Institution.DoesNotExist:
                return JsonResponse({"error": "Institution not found"}, status=404)

            # Get current time in IST (UTC+5:30)
            current_time = timezone.now() + timedelta(hours=5, minutes=30)

            # Find active subscription for this institution using InstitutionSubscription
            active_subscription = InstitutionSubscription.objects.filter(
                user=user,
                subscription_plan__institution=institution,
                status='valid'
            ).first()

            if not active_subscription:
                return JsonResponse({"error": "User does not have an active subscription"}, status=403)

            # Find latest attendance for this user and institution
            latest_attendance = CoachingAttendance.objects.filter(
                user=user,
                institution=institution
            ).order_by('-check_in_time').first()

            # Handle time comparisons with date adjustments
            start_time = active_subscription.start_time
            end_time = active_subscription.end_time

            if start_time and end_time and start_time > end_time:
                end_date = active_subscription.start_date + timedelta(days=1)
                start_date = active_subscription.start_date
            else:
                start_date = active_subscription.start_date
                end_date = active_subscription.start_date

            # Create datetime objects with adjusted dates
            if start_time and end_time:
                start_datetime = timezone.make_aware(datetime.combine(start_date, start_time))
                end_datetime = timezone.make_aware(datetime.combine(end_date, end_time))
                current_datetime = timezone.make_aware(datetime.combine(current_time.date(), current_time.time()))
                is_within_time = (start_datetime <= current_datetime <= end_datetime)
            else:
                is_within_time = True  # If no time window, always allow

            check_out_color = 0 if is_within_time else 1
            current_time = timezone.now()
            ist_time = current_time + timedelta(hours=5, minutes=30)

            if not latest_attendance or latest_attendance.check_out_time:
                # New check-in
                attendance = CoachingAttendance.objects.create(
                    user=user,
                    institution=institution,
                    check_in_time=current_time,
                    check_in_color=check_out_color,
                    check_out_color=0,
                    # nfc_id=nfc_serial  # Remove this if CoachingAttendance does not have nfc_id
                )
                return JsonResponse({
                    "message": f"Checked in: {user.get_full_name()}",
                    "action": "checkin",
                    "date": current_time.date().isoformat(),
                    "time": ist_time.strftime("%H:%M:%S"),
                })
            else:
                # Check-out
                latest_attendance.check_out_time = current_time
                latest_attendance.check_out_color = check_out_color
                latest_attendance.save()
                return JsonResponse({
                    "message": f"Checked out: {user.get_full_name()}",
                    "action": "checkout",
                    "date": current_time.date().isoformat(),
                    "time": ist_time.strftime("%H:%M:%S"),
                })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
