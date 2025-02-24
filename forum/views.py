from django.shortcuts import render, redirect

# Create your views here.

def index_redirect(request):
    return redirect("index")

def index(request):
    return render(request, "index.html")

def faq(request):
    return render(request, "faq.html")