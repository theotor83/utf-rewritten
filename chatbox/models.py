from django.db import models
from django.contrib.auth.models import User
from chatbox.chatboxmessagehandler import ChatboxMessageHandler, ChatboxSaveError

# Create your models here.

chatbox_message_handler = ChatboxMessageHandler()  # ? I don't know if that's bad practice

class Chatbox(models.Model):
    """
    This is most likely a REALLY bad practice. This is only to have a title and a list of current connected users.
    This should stay a singleton.
    """
    id = models.AutoField(primary_key=True)
    title = models.TextField(max_length=65535)
    connected_users = models.ManyToManyField(User, related_name='connected_users')

class ChatboxMessageManager(models.Manager):

    @staticmethod
    def create_message(author, text, quoted_message=None, created_time=None): # This could be inside a Manager class...
        return ChatboxMessage.objects.create(author=author, text=text, quoted_message=quoted_message, created_time=created_time)


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
            chatbox_message_handler.check_message_pre_save(self)
        except Exception as e:
            if isinstance(e, ChatboxSaveError):
                print(f"Message cannot be saved for valid pre-save reason : {e}")
                return
            elif isinstance(e, ValueError):
                print(f"Message cannot be saved for weird pre-save reason : {e}")
                return

        super().save(*args, **kwargs)

        try:
            chatbox_message_handler.check_message_post_save(self)
        except Exception as e:
            if isinstance(e, ChatboxSaveError):
                print(f"Message cannot be saved for valid post-save reason : {e}")
                try: # TODO [9]: Find a better way to do this, this looks very wrong but at least it works
                    self.delete()
                    print("Message deleted successfully after failed post-save check")
                except Exception as delete_exception:
                    print(f"Message could not be deleted after failed post-save check : {delete_exception}")
            elif isinstance(e, ValueError):
                print(f"Message cannot be saved for weird post-save reason : {e}")
                try:
                    self.delete()
                    print("Message deleted successfully after failed post-save check")
                except Exception as delete_exception:
                    print(f"Message could not be deleted after failed post-save check : {delete_exception}")

