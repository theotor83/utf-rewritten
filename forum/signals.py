import redis
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Topic, Category, Post
from utf.utils import cprint

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@receiver(post_save, sender=Post)
def send_watch_topic_notification(sender, instance, created, **kwargs):
    """
    After a post is created, notify all users watching the topic/subforum/category.
    """
    if created:
        topic = instance.topic
        for user in topic.watchers.all():
            channel_name = f"user_notifications_{user.id}"

            notification = {
                'message': f'Un [url=http://127.0.0.1:8000{instance.get_absolute_url}]nouveau post[/url] a été publié !'
            }
            redis_client.publish(channel_name, json.dumps(notification))
            cprint(f"Published notification for User {user.id} to channel {channel_name}")