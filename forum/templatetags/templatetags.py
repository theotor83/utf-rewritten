# forum/templatetags/templatetags.py

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re
import base64
import urllib.parse
from django.utils import timezone
from archive.models import *

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
    return ArchivePost.objects.filter(created_time__lte=before_datetime if before_datetime else timezone.now()).count()

@register.simple_tag
def get_total_users(before_datetime=None):
    """A template tag to get the total number of users in the forum, with support for past dates."""
    return FakeUser.objects.filter(date_joined__lte=before_datetime if before_datetime else timezone.now()).count()

@register.simple_tag
def get_latest_user(before_datetime=None):
    """A template tag to get the latest user in the forum, with support for past dates."""
    return FakeUser.objects.filter(date_joined__lte=before_datetime if before_datetime else timezone.now()).order_by('date_joined', 'id').last()

@register.simple_tag
def get_user_age_in_past(user, before_datetime=None):
    """A template tag to get the latest user in the forum, with support for past dates."""
    return user.archiveprofile.get_user_age_past(before_datetime=before_datetime)

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
    return topic.get_latest_message_before(before_datetime=before_datetime)

@register.simple_tag
def past_total_replies(topic, before_datetime=None):
    """A template tag to get the total number of replies in a topic, with support for past dates."""
    # WARNING: This tag doesn't work as expected for now, because it doesn't count nested replies.
    replies_count = 0
    for child in topic.archive_children.filter(created_time__lte=before_datetime if before_datetime else timezone.now()):
        # if child.is_sub_forum:
            # # If the child is a subforum, we count its children recursively (only for one level of nesting, because the archive only supports one level of nesting)
            # replies_count += ArchivePost.objects.filter(topic=child.archive_children, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
        replies_count += ArchivePost.objects.filter(topic=child, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
    return replies_count

@register.simple_tag
def past_total_children(topic, before_datetime=None):
    """A template tag to get the total number of children and nested replies in a subforum, with support for past dates."""
    if not topic.is_sub_forum:
        return 0
    return ArchiveTopic.objects.filter(parent=topic, created_time__lte=before_datetime if before_datetime else timezone.now()).count()