from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_redirect, name='index-redirect'),
    path('index/', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
    path('register/regulation/', views.register_regulation, name='register-regulation'),
    path('register/', views.register, name='register'),
    path('member_not_found/', views.member_not_found, name='member-not-found'),
    path('login/', views.login_view, name='login-view'),
    path('logout/', views.logout_view, name='logout-view'),
    path('profile/<int:userid>/', views.profile_details, name='profile-details'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)