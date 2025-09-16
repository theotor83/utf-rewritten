from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views as token_views

urlpatterns = [
    path('posts_list/', views.posts_list, name='archive-api-posts-list'),
    path('profile/<int:userid>/', views.profile_details, name='archive-api-profile-details'),
    path('api-token-auth/', token_views.obtain_auth_token, name='archive-api-token-auth'),
    path('post/<int:postid>/', views.post_details, name='archive-api-post-details'),
]
