from django.utils.timezone import now
from .models import Profile, Forum
from django.utils import timezone
from datetime import timedelta

def base_context(request):
    """
    This function is being called every time a template containing base.html is rendered.
    """
    UTF, _ = Forum.objects.get_or_create(name='UTF')
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.last_login and timezone.now() - profile.last_login >= timedelta(minutes=15):
                profile.last_login = now()
                profile.save(update_fields=["last_login"])
                print(f"User {request.user} logged in at {profile.last_login}")
                intervalle = now() - timedelta(minutes=30)
                online_count = Profile.objects.filter(last_login__gte=intervalle).count()
                if UTF.online_record < online_count:
                    UTF.online_record = online_count
                    UTF.online_record_date = now()
                    print(f"New online record: {online_count} at {UTF.online_record_date}")
                    UTF.save(update_fields=["online_record", "online_record_date"])
            else:
                print(f"User is still online at {profile.last_login}")
        except Profile.DoesNotExist:
            pass  # In case the user does not have a profile yet
    return {}
