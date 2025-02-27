from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm, ProfileForm
from .models import Profile

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
            
            login(request, user)
            return redirect('index')
    else:
        user_form = UserRegisterForm()
        profile_form = ProfileForm()

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'register.html', context)

def member_not_found(request):
    return render(request,'member_not_found.html')