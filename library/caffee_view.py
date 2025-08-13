from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import CafeForm
from .models import Cafe
 
@login_required
def register_cafe(request):
    if request.method == 'POST':
        # Pass the user as the owner if not present in POST data
        post_data = request.POST.copy()
        # Remove 'owner' from POST if present, always set to current user
        if 'owner' in post_data:
            post_data.pop('owner')
        form = CafeForm(post_data)
        if form.is_valid():
            cafe = form.save(commit=False)
            # Ensure the user is set as both owner and user (if both fields exist)
            cafe.owner = request.user
            if hasattr(cafe, 'user_id'):
                cafe.user = request.user
            cafe.save()
            return render(request, 'caffee/caffee_registration_success.html')
    else:
        form = CafeForm()
    return render(request, 'caffee/register_cafe.html', {'form': form})

@login_required
def cafe_dashboard(request, cafe_id):
    try:
        cafe = Cafe.objects.get(id=cafe_id, user=request.user)
        if cafe.status != 'approved':
            return HttpResponseForbidden("This cafe is not approved yet.")
    except Cafe.DoesNotExist:
        cafe = None
    return render(request, 'caffee/caffee_dashboard.html', {'cafes': [cafe] if cafe else []})