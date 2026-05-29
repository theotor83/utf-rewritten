from django.db import models
from django.contrib.auth.models import User
from chatbox.chatboxmessagechecker import ChatboxMessageChecker, ChatboxSaveError

# Create your models here.

chatbox_message_checker = ChatboxMessageChecker()  # ? I don't know if that's bad practice

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

    def save(self, *args, **kwargs):
        try:
            chatbox_message_checker.check_message(self)
        except Exception as e:
            if isinstance(e, ChatboxSaveError):
                print(f"Message cannot be saved for valid reason : {e}")
                return
            elif isinstance(e, ValueError):
                print(f"Message cannot be saved for weird reason : {e}")
                return
        super().save(*args, **kwargs)
        # TODO [10]: Make a post save checker to check IDs, dates etc.