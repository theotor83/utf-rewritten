from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, ProfileForm
from .models import Profile, ForumGroup, User
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse

# Create your views here.

def index_redirect(request):
    return redirect("index")

def index(request):
    return render(request, "index.html")

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

def member_not_found(request):
    return render(request,'member_not_found.html')

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request): #TODO [7] : Add confirmation
    logout(request)
    return redirect("index")

def profile_details(request, userid):
    try :
        requested_user = User.objects.get(id=userid)
        return render(request, "profile_page.html", {"req_user":requested_user})
    except:
        return render(request, "member_not_found.html")