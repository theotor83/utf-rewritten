from django.apps import AppConfig


class ChatboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbox'

    def ready(self):
        """
        This method has been made with AI. The goal is to clean the connected users of the chatbox when the server starts.
        """
        import sys
        if 'manage.py' in sys.argv and ('makemigrations' in sys.argv or 'migrate' in sys.argv):
            return

        try:
            from chatbox.models import Chatbox
            chatbox = Chatbox.objects.filter(id=1).first()
            if chatbox:
                chatbox.connected_users.clear()
        except Exception:
            pass
