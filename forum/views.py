import locale
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, ProfileForm
from .models import Profile, ForumGroup, User, Category, Post, Topic
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _

# Functions used by views

def generate_pagination(current_page, max_page):
    if max_page == 1:
        return [1]
    
    first_part = [1, 2, 3] if max_page >= 3 else []
    last_part = [max_page - 1, max_page] if max_page >= 3 else []
    
    middle_part = []
    for p in [current_page - 1, current_page, current_page + 1]:
        if 1 <= p <= max_page:
            middle_part.append(p)
    
    pages = sorted(set(first_part + middle_part + last_part))
    
    pagination = []
    prev = None
    for page in pages:
        if prev is not None and page > prev + 1:
            pagination.append("...")
        pagination.append(page)
        prev = page
    
    return pagination

# Create your views here.

def index_redirect(request):
    return redirect("index")

def index(request):
    # Set the locale to French
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

    # Get the current time and format it
    now = timezone.localtime(timezone.now())
    formatted_date = now.strftime("%a %d %b - %H:%M (%Y)").capitalize() #TODO: [1] Format this date to day with 3 letters and no dot, and month with a capital letter and 3 letters only

    # Create the context with translated text
    context = {
        'current_date': _(f"La date/heure actuelle est {formatted_date}"),
        "categories": Category.objects.all()
    }

    return render(request, "index.html", context)

def faq(request):
    return render(request, "faq.html")

def register_regulation(request):
    return render(request, "register_regulation.html")

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save User first
            user = user_form.save()
            
            # Save Profile linked to the User
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            try:
                outsider_group = ForumGroup.objects.get(name="Outsider")
                profile.groups.add(outsider_group)
            except ForumGroup.DoesNotExist:
                return HttpResponse(status=500)
            login(request, user)
            return redirect('index')
    else:
        user_form = UserRegisterForm()
        profile_form = ProfileForm()

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'register.html', context)

def error_page(request, error_title, error_message):
    context = {"error_title":error_title, "error_message":error_message}
    return render(request, "error_page.html", context)

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("index")

def profile_details(request, userid):
    try :
        requested_user = User.objects.get(id=userid)
        return render(request, "profile_page.html", {"req_user":requested_user})
    except:
        return error_page(request, "Informations", "Désolé, mais cet utilisateur n'existe pas.")
    
def member_list(request):
    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page
    max_page  = ((User.objects.count()) // members_per_page) + 1

    members = User.objects.all().order_by('id')[limit - members_per_page : limit]

    pagination = generate_pagination(current_page, max_page)

    return render(request, "memberlist.html", {"members" : members, "current_page" : current_page, "max_page":max_page, "pagination":pagination})