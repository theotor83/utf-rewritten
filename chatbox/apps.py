from django.apps import AppConfig

class ChatboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbox'

    def ready(self):
        import chatbox.signals # In order to load the signals for later use