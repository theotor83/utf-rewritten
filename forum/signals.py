import redis
import json
import os
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Topic, Category, Post
from utf.utils import cprint

logger = logging.getLogger(__name__)

# Configure Redis client based on environment
DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False') == 'True'

try:
    if DEVELOPMENT_MODE:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False, socket_connect_timeout=5)
        logger.info("Redis client initialized for DEVELOPMENT mode (localhost:6379)")
    else:
        REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(REDIS_URL, decode_responses=False, socket_connect_timeout=5)
        # Test connection immediately
        redis_client.ping()
        logger.info(f"Redis client initialized for PRODUCTION mode via REDIS_URL")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    logger.error(f"DEVELOPMENT_MODE={DEVELOPMENT_MODE}, REDIS_URL={os.getenv('REDIS_URL', 'NOT_SET')}")
    # Create a dummy client that will fail gracefully
    redis_client = None
except Exception as e:
    logger.error(f"Unexpected error initializing Redis: {e}")
    redis_client = None

@receiver(post_save, sender=Post)
def send_watched_topic_notification_post(sender, instance, created, **kwargs):
    """
    After a post is created, notify all users watching the topic/subforum/category.
    """
    if created and instance.get_relative_id != 1:  # Only notify for replies, not the first post in a topic
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
            
            # Publish notification to Redis (with error handling)
            if redis_client:
                try:
                    redis_client.publish(channel_name, json.dumps(notification))
                    cprint(f"Published notification for User {user_id} to channel {channel_name}")
                except Exception as e:
                    logger.error(f"Failed to publish notification to Redis: {e}")
            else:
                logger.warning("Redis client not available, skipping notification")
            
            already_notified_user_ids.append(user_id)

@receiver(post_save, sender=Topic)
def send_watched_topic_notification_topic(sender, instance, created, **kwargs):
    """
    After a topic is created, notify all users watching the subforum/category.
    """
    if created:
        topic = instance

        watchers_id_list = []
        for user in topic.category.watchers.all():
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
                'message': f"{instance.author.username} a créé un nouveau sujet \"{topic.get_short_title()}\".",
                'text_preview': f"Cliquez ici pour voir le sujet.",
                'post_url': instance.get_absolute_url,
                'author_username': instance.author.username,
                'topic_full_title': topic.title,
            }
            
            # Publish notification to Redis (with error handling)
            if redis_client:
                try:
                    redis_client.publish(channel_name, json.dumps(notification))
                    cprint(f"Published notification for User {user_id} to channel {channel_name}")
                except Exception as e:
                    logger.error(f"Failed to publish notification to Redis: {e}")
            else:
                logger.warning("Redis client not available, skipping notification")
            
            already_notified_user_ids.append(user_id)