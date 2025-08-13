from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CafeForm
from .models import Cafe

@login_required
def register_cafe(request):
    if request.method == 'POST':
        form = CafeForm(request.POST)
        if form.is_valid():
            cafe = form.save(commit=False)
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
    except Cafe.DoesNotExist:
        cafe = None
    return render(request, 'caffee/caffee dashboard.html', {'cafes': [cafe] if cafe else []})