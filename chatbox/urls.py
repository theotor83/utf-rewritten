from django.urls import path
from chatbox import views

urlpatterns = [
    path('connect/', views.connect, name='chatbox-connect'),
    path('message/', views.message, name='chatbox-message'),
    path('message/<int:messageid>/', views.message_details, name='chatbox-message-details'),
    path('messages/', views.messages, name='chatbox-messages'),
    path('test/', views.test_chatbox, name='chatbox-test'),
]