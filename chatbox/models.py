from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ChatboxMessage(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbox_messages')
    text = models.TextField(max_length=65535)
    created_time = models.DateTimeField(auto_now_add=True)
    quoted_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='quoted_by')

    def __str__(self):
        return f"Chatbox message {self.id} by {self.author.username} at {self.created_time}"
    
    class Meta:
        ordering = ['created_time']