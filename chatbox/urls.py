from django.urls import path
from chatbox import views

urlpatterns = [
    path('message/<int:messageid>/', views.message_details, name='chatbox-message-details'),
    path('messages/', views.messages, name='chatbox-messages'),
    path('test/', views.test_chatbox, name='chatbox-test'),
    path('users', views.users, name='chatbox-users'),
]