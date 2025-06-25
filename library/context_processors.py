from .models import Gym

def approved_gym(request):
    """
    Adds the user's first approved gym to the context.
    """
    if request.user.is_authenticated:
        first_approved_gym = Gym.objects.filter(owner=request.user, is_approved=True).first()
        return {'approved_gym': first_approved_gym}
    return {} 