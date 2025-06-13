# Django core imports
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging
from django.utils.timezone import now
from .forms import InstitutionRegistrationForm

# Set up logging
logger = logging.getLogger(__name__)

def coaching_dashboard(request):
    return render(request, 'coaching/coaching_dashboard.html')

@login_required
def register_coaching_form(request):
    """Handle coaching center registration"""
    if request.method == 'POST':
        form = InstitutionRegistrationForm(request.POST)
        if form.is_valid():
            Institution = form.save(commit=False)
            Institution.business_type = 'Institution'
            Institution.save()
            return redirect('enrollment_success_coaching')
    else:
        form = InstitutionRegistrationForm()
    return render(request, 'coaching/register_coaching_form.html', {'form': form})

def enrollment_success(request):
    return render(request, 'library/enrollment_success.html')