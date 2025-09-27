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
    path('topic/<int:topicid>/', views.topic_details, name='archive-api-topic-details'),
    path('post_details/<int:postid>/', views.post_details, name='api-post-details'),
    path('category/<int:categoryid>/', views.category, name='api-category'),
    path('category_details/<int:categoryid>/', views.category_details, name='api-category-details'),
]
