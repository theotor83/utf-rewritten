from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_redirect, name='index-redirect'),
    path('index/', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
    path('register/regulation', views.register_regulation, name='register-regulation'),
    path('register', views.register, name='register'),
    path('member_not_found', views.member_not_found, name='member-not-scared'),
    path('login', views.login_view, name='login-view'),
    path('logout', views.logout_view, name='logout-view'),
]
