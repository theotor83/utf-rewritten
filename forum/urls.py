from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_redirect, name='index-redirect'),
    path('index/', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
]
