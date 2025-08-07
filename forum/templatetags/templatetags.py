# forum/templatetags/templatetags.py

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.core.cache import cache
import re
import base64
import urllib.parse
import hashlib
from django.utils import timezone
from archive.models import *
import random
from ..views_context_processors import return_random_color

# This is a file for all the template tags that were too hard to make work with precise_bbcode.
# It is not a good practice to use this file, and will probably get very messy later on, but it is easier to understand for now.

register = template.Library()

@register.filter
def process_video_tags(value):
    """Convert video tags to placeholders with base64-encoded URLs"""
    pattern = r'\[video\](.*?)\[/video\]'
    
    def replace_video_tag(match):
        url = match.group(1).strip()
        # Base64 encode the URL to prevent it from being recognized as a URL
        encoded_url = base64.b64encode(url.encode('utf-8')).decode('utf-8')
        return f'[VIDEO_ENCODED]{encoded_url}[/VIDEO_ENCODED]'
    
    # Replace all video tags with encoded placeholders
    processed_text = re.sub(pattern, replace_video_tag, value)
    return processed_text

@register.filter
def finalize_video_tags(value):
    """Convert encoded placeholders back to video tags with security validation"""
    pattern = r'\[VIDEO_ENCODED\](.*?)\[/VIDEO_ENCODED\]'
    
    def replace_placeholder(match):
        encoded_url = match.group(1)
        try:
            # Decode the base64 URL
            url = base64.b64decode(encoded_url.encode('utf-8')).decode('utf-8')
            
            url_is_safe = False
            
            # More thorough URL validation
            if url.startswith('https://'):
                # Parse the URL to validate its structure
                parsed_url = urllib.parse.urlparse(url)
                # Check if it has a valid netloc (domain) and no suspicious components
                if parsed_url.netloc and not any(c in url for c in ['"', "'", '<', '>', ';', ' ']):
                    url_is_safe = True
            
            if url_is_safe:
                # Escape the URL to prevent XSS
                safe_url = escape(url)
                return f'<video controls style="max-width: 500px; max-height: 500px;" ><source src="{safe_url}" type="video/mp4"></video>'
            else:
                return "[URL vidéo invalide]"
                
        except Exception as e:
            # Handle decoding errors safely
            return f"[Error processing video: {escape(str(e))}]"
    
    processed_text = re.sub(pattern, replace_placeholder, value)
    return mark_safe(processed_text)

@register.filter
def intspace(value):
    """
    Formats an integer number with a space as a thousands separator.
    If the value is not an integer, it is returned unchanged.
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    # Format the number with commas then replace commas with spaces.
    formatted = "{:,}".format(value).replace(",", " ")
    return formatted


# =====================================================
# ==================== Simple tags ====================
# =====================================================

# ===== Time machine feature =====

# Index page template tags

@register.simple_tag
def get_total_messages(before_datetime=None):
    """A template tag to get the total number of messages in the forum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"total_messages_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_total_messages = ArchivePost.objects.filter(created_time__lte=before_datetime if before_datetime else timezone.now()).count()

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_total_messages, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_total_messages} messages")
    return past_total_messages

@register.simple_tag
def get_total_users(before_datetime=None):
    """A template tag to get the total number of users in the forum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"total_users_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_total_users = FakeUser.objects.filter(date_joined__lte=before_datetime if before_datetime else timezone.now()).count()

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_total_users, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_total_users} users")
    return past_total_users

@register.simple_tag
def get_latest_user(before_datetime=None):
    """A template tag to get the latest user in the forum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"latest_user_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_latest_user = FakeUser.objects.filter(date_joined__lte=before_datetime if before_datetime else timezone.now()).order_by('date_joined', 'id').last()

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_latest_user, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_latest_user}")
    return past_latest_user

@register.simple_tag
def get_user_age_in_past(user, before_datetime=None):
    """A template tag to get the latest user in the forum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"user_{user.id}_age_at_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_age = user.archiveprofile.get_user_age_past(before_datetime=before_datetime)

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_age, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_age}")
    return past_age

@register.simple_tag
def return_season_video(fake_datetime=None):
    """A template tag to return the current season based on the date, with support for past dates."""
    if fake_datetime is None:
        fake_datetime = timezone.now()
    
    month = fake_datetime.month
    day = fake_datetime.day

    if (month == 3 and day >= 20) or (month in [4, 5]) or (month == 6 and day < 21):
        return "https://youtube.com/embed/QXmOmkRuHUc?loop=1&amp;autoplay=0&amp;controls=0" # Spring
    elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day < 22):
        return "https://youtube.com/embed/iBcY95m51Rw?loop=1&amp;autoplay=0&amp;controls=0" # Summer
    elif (month == 9 and day >= 22) or (month in [10, 11]) or (month == 12 and day < 21):
        return "https://youtube.com/embed/fcNq5FlMclU?loop=1&amp;autoplay=0&amp;controls=0" # Autumn
    else:
        return "https://youtube.com/embed/SKvlsQaukOg?loop=1&amp;autoplay=0&amp;controls=0" # Winter

# Index/subforum page template tags

@register.simple_tag
def latest_topic_message(topic, before_datetime=None):
    """A template tag to call the get_latest_message method on a topic, with support for past dates."""
    # Create cache key based on topic ID and datetime
    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"topic_{topic.id}_latest_message_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_latest_message = topic.get_latest_message_before(before_datetime=before_datetime)

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_latest_message, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_latest_message}")
    return past_latest_message

@register.simple_tag
def past_total_replies(topic, before_datetime=None):
    """A template tag to get the total number of replies in a topic, with support for past dates."""
    # Create cache key based on topic ID and datetime
    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"past_total_replies_{topic.id}_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    # WARNING: This tag doesn't work as expected for now, because it doesn't count nested replies.
    replies_count = 0
    if topic.is_sub_forum:
        for child in topic.archive_children.filter(created_time__lte=before_datetime if before_datetime else timezone.now()):
            # if child.is_sub_forum:
                # # If the child is a subforum, we count its children recursively (only for one level of nesting, because the archive only supports one level of nesting)
                # replies_count += ArchivePost.objects.filter(topic=child.archive_children, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
            replies_count += ArchivePost.objects.filter(topic=child, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
        #print(f"Total replies in subforum {topic.id} before {before_datetime}: {replies_count}")
    else:
        # If the topic is not a subforum, we count the replies in the topic itself.
        replies_count = ArchivePost.objects.filter(topic=topic, created_time__lte=before_datetime if before_datetime else timezone.now()).count() - 1 # Subtract 1 to not count the first post as a reply.
        #print(f"Total replies in topic {topic.id} before {before_datetime}: {replies_count}")
    
    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, replies_count, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {replies_count} replies")
    return replies_count

@register.simple_tag
def past_total_children(topic, before_datetime=None):
    """A template tag to get the total number of children and nested replies in a subforum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"past_total_children_{topic.id}_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    # Perform the database query
    if not topic.is_sub_forum:
        return 0
    total_children = ArchiveTopic.objects.filter(parent=topic, created_time__lte=before_datetime if before_datetime else timezone.now()).count()

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, total_children, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {total_children} children")
    return total_children

# Topic page template tags

@register.simple_tag
def get_user_message_count(user, before_datetime=None):
    """A template tag to get the total number of messages of a user, with support for past dates."""
    # Create cache key based on user ID and datetime
    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"user_message_count_{user.id}_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    # Perform the database query
    message_count = ArchivePost.objects.filter(author=user, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
    
    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, message_count, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {message_count} messages")
    return message_count

# All/any page template tags

@register.simple_tag
def get_correct_group(user, before_datetime=None): # TODO: [8] Reformat this tag into the views. Could gain up to 1000ms of performance, but the caching is fine.
    """A template tag to get the correct group of a user, with support for past dates."""
    # Create cache key based on user ID and datetime
    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"user_correct_group_{user.id}_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    user_group = user.archiveprofile.get_top_group
    if not user_group:
        result = None
    elif user_group.name == "Outsider" or user_group.priority > 75: # Every group with priority > 75 is a "special user" group, like staff or custom group.
        result = user_group
    else:
        # If the user is a "regular user", we need to calculate the user's message count before the given date, and return the group based on that.
        message_count = ArchivePost.objects.filter(author=user, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
        # Now, get the group with the highest "minimum_messages" value that is less than or equal to the message count.
        group = ArchiveForumGroup.objects.filter(is_messages_group=True, minimum_messages__lte=message_count).first()
        #print(f"User {user.username} has {message_count} messages, group: {group.name if group else 'None'}")
        result = group if group else user_group
    
    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, result, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {result}")
    return result

@register.simple_tag
def get_user_random_color(username):
    return return_random_color(seed=username)

@register.filter
def timestamp(value): # To be used on DateTimeField values in templates
    return value.timestamp() if value else None