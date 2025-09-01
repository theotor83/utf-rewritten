from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('posts_list/', views.posts_list, name='posts-list'),
    path('profile/<int:userid>/', views.profile_details, name='profile-details'),
]