import redis
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Topic, Category, Post
from utf.utils import cprint

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@receiver(post_save, sender=Post)
def send_watched_topic_notification(sender, instance, created, **kwargs):
    """
    After a post is created, notify all users watching the topic/subforum/category.
    """
    if created:
        topic = instance.topic

        watchers_id_list = []
        for user in topic.watchers.all():
            watchers_id_list.append(user.id)

        for user in topic.category.watchers.all():
            if user.id not in watchers_id_list:
                watchers_id_list.append(user.id)

        parent = topic.parent
        while parent:
            for user in parent.watchers.all():
                if user.id not in watchers_id_list:
                    watchers_id_list.append(user.id)
            parent = parent.parent
        
        already_notified_user_ids = [instance.author.id]

        for user_id in watchers_id_list:
            if user_id in already_notified_user_ids:
                continue
            channel_name = f"user_notifications_{user_id}"

            notification = {
                'message': f"{instance.author.username} a posté une réponse sur \"{topic.get_short_title()}\".",
                'text_preview': instance.get_short_text(100),
                'post_url': instance.get_absolute_url,
                'author_username': instance.author.username,
                'topic_full_title': topic.title,
            }
            redis_client.publish(channel_name, json.dumps(notification))
            cprint(f"Published notification for User {user_id} to channel {channel_name}")
            already_notified_user_ids.append(user_id)