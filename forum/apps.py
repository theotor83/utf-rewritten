from django.apps import AppConfig
from django.db.models.signals import post_migrate

def register_bbcode_tags(sender, **kwargs):
    # Import and register BBCode tags here
    from forum import bbcode_tags
    bbcode_tags.register_all()

class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'

    def ready(self):
        # Connect to post_migrate signal instead of importing directly
        post_migrate.connect(register_bbcode_tags, sender=self)
