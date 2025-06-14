# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from .forms import InstitutionRegistrationForm, InstitutionCouponForm, UPIForm, InstitutionBannerForm
from django.contrib import messages
from .models import Institution, CustomUser, InstitutionCoupon, InstitutionReview, InstitutionImage, InstitutionBanner
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import models
import re
from django.db import transaction

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
        'institution': institution
    })

def public_institute_details(request, uid):
    """Public view of institution details"""
    institution = get_object_or_404(Institution, uid=uid)
    if not institution.is_approved:
        messages.error(request, "This institution is not yet approved.")
        return redirect('home')
    return render(request, 'coaching/public_institute_details.html', {
        'institution': institution
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
                form.save()
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