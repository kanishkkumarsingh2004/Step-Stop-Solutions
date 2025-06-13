# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from .forms import InstitutionRegistrationForm, InstitutionCouponForm
from django.contrib import messages
from .models import Institution, CustomUser, InstitutionCoupon
from django.http import JsonResponse
from django.views.decorators.http import require_POST

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
        
        return render(request, 'coaching/coaching_dashboard.html', {
            'institution': institution,
            'active_coupons_count': active_coupons_count,
            'total_coupons_count': total_coupons_count,
            'expired_coupons_count': expired_coupons_count,
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
        return redirect('coaching_dashboard')
    
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
                institution.save()
                
                messages.success(request, "Institution profile updated successfully!")
                return redirect('coaching_dashboard')
            except Exception as e:
                logger.error(f"Error updating institution: {str(e)}")
                messages.error(request, "An error occurred while updating the institution. Please try again.")
        else:
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