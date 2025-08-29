# forum/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, is_naive
from django.utils.text import slugify
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from collections import deque
import os
import uuid
from django.utils import timezone
from precise_bbcode.models import SmileyTag
import datetime
from django.db.models import Count, Sum
import re
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

# def profile_picture_upload_path(instance, filename):
#     """Generate a file path with username, original filename, and a 4-character UUID"""
#     username = instance.user.username  # Assuming a OneToOne relation with User
#     ext = filename.split('.')[-1]  # Get the file extension
#     base_filename = os.path.splitext(filename)[0]  # Get filename without extension
#     short_uuid = uuid.uuid4().hex[:4]  # Generate a 4-character UUID
#     new_filename = f"{username}_{base_filename}_{short_uuid}.{ext}"  # Construct new filename
#     return os.path.join("images/profile_picture", new_filename)

class SafeDateTimeField(models.DateTimeField):
    """
    Custom DateTimeField that handles potential database errors
    on retrieval by returning a default date (e.g., 1900-01-01).
    """
    def get_prep_value(self, value):
        # Ensure value is valid before saving
        if value:
            # Basic check for year range before preparing for DB
            # You might adjust the lower bound (e.g., 1) if needed
            min_allowed_year = 1
            if hasattr(value, 'year') and value.year < min_allowed_year:
                 raise ValidationError(f"Year {value.year} is out of allowed range (>= {min_allowed_year}).")
        return super().get_prep_value(value)

    def from_db_value(self, value, expression, connection):
        """
        Overrides the default method to handle invalid dates from DB.
        """
        if value is None:
            return value
        try:
            # Try default conversion first
            return super().from_db_value(value, expression, connection)
        except ValueError:
            # If conversion fails (e.g., year -1), return a placeholder
            placeholder = datetime.datetime(1900, 1, 1)
            # Make placeholder timezone-aware if settings.USE_TZ is True
            if timezone.get_current_timezone() and is_naive(placeholder):
                 return make_aware(placeholder, timezone.get_current_timezone())
            return placeholder

    def to_python(self, value):
        """
        Overrides the default method to handle invalid dates during deserialization.
        """
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
             # Convert date to datetime if necessary
             dt_value = datetime.datetime.combine(value, datetime.time.min)
             if timezone.get_current_timezone() and is_naive(dt_value):
                 return make_aware(dt_value, timezone.get_current_timezone())
             return dt_value

        try:
            # Try default conversion first
            parsed_value = super().to_python(value)
            # Ensure timezone awareness if needed
            if timezone.get_current_timezone() and is_naive(parsed_value):
                 return make_aware(parsed_value, timezone.get_current_timezone())
            return parsed_value
        except (ValueError, TypeError):
            # If conversion fails, return a placeholder
            placeholder = datetime.datetime(1900, 1, 1)
            if timezone.get_current_timezone() and is_naive(placeholder):
                 return make_aware(placeholder, timezone.get_current_timezone())
            return placeholder

def mark_all_topics_read_for_user(user):
    """Mark all topics as read for the user."""
    if not user.is_authenticated:
        return

    # Circular import avoided by using local reference
    from .models import Topic, TopicReadStatus
    
    # Get all topics in the forum
    all_topics = Topic.objects.all()

    # Iterate through each topic and mark it as read for the user
    for topic in all_topics:
        TopicReadStatus.objects.update_or_create(
            user=user,
            topic=topic,
            defaults={'last_read': timezone.now()}
        )

def strip_bbcode(text: str) -> str:
    """
    Strips BBCode from a given text, converting some tags to a raw text representation.

    - [hr] is converted to a horizontal line.
    - [quote] and [quote=author] are converted to "> {text}" blocks.
    - [youtube] and [yt] are converted to full YouTube links.
    - [spoiler] content is replaced by black square emojis (1 per 3 chars).
    - Styling tags are removed.
    """
    if not isinstance(text, str):
        return ""

    # Spoiler tag handler function
    def replace_spoiler_with_emojis(match):
        content = match.group(1)
        # Calculate the number of emojis: 1 for every 3 characters
        num_emojis = len(content) // 3
        return '⬛' * num_emojis

    # [spoiler=title]content[/spoiler] -> black square emojis
    # This must be run first as it captures and replaces content.
    text = re.sub(
        r'\[spoiler(?:=.*?)?\](.*?)\[/spoiler\]',
        replace_spoiler_with_emojis,
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # [hr] -> horizontal line
    text = re.sub(r'\[hr\]', '\n--------\n', text, flags=re.IGNORECASE)

    # [youtube] and [yt] -> YouTube link
    text = re.sub(r'\[youtube\](.*?)\[/youtube\]', r'https://www.youtube.com/watch?v=\1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[yt\](.*?)\[/yt\]', r'https://www.youtube.com/watch?v=\1', text, flags=re.DOTALL | re.IGNORECASE)

    # [quote=author]content[/quote] -> > content
    # Replace opening quote tag with "> "
    text = re.sub(r'\[quote(?:=.*?)?\]', '> ', text, flags=re.IGNORECASE | re.DOTALL)
    # Remove closing quote tag completely
    text = re.sub(r'\[/quote\]', '', text, flags=re.IGNORECASE | re.DOTALL)

    # List of tags to be stripped, keeping the content.
    tags_to_strip = [
        'font', 'size', 'pxsize', 'color', 'justify', 'code', 'marquee', 'rawtext',
        'b', 'i', 'u', 's', 'url', 'email', 'img', 'list', 'li', r'\*', 
        '*', 'code', 'center'
    ]
    
    # Build a single regex to remove all the tags in the list.
    tag_names = '|'.join(tags_to_strip)
    pattern = r'\[/?(' + tag_names + r')(?:=[^\]]*)?\]'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Clean up artifacts like a ">" followed by a newline and then text.
    text = re.sub(r'>\s*\n', '> ', text)

    # Trim leading/trailing whitespace from the whole text
    text = text.strip()

    return text

# Choices for CharField(choices = ...)

TYPE_CHOICES = (
    ("pacifist", "Pacifiste"),
    ("neutral", "Neutre"),
    ("genocide", "Génocidaire")
)

ZODIAC_CHOICES = (
    ("capricorne", "Capricorne (22déc-19jan)"),
    ("verseau", "Verseau (20jan-19fev)"),
    ("poissons", "Poissons(20fev-20mar)"),
    ("belier", "Bélier (21mar-19avr)"),
    ("taureau", "Taureau (20avr-20mai)"),
    ("gemeaux", "Gémeaux (21mai-20juin)"),
    ("cancer", "Cancer (21juin-23juil)"),
    ("lion", "Lion (24juil-23aoû)"),
    ("vierge", "Vierge (24aoû-22sep)"),
    ("balance", "Balance (23sep-22oct)"),
    ("scorpion", "Scorpion (23oct-21nov)"),
    ("sagittaire", "Sagittaire (22nov-21déc)"),
    ("", "Aucun"),
)

GENDER_CHOICES = (
    ("male", "Masculin"),
    ("female", "Féminin")
)

ICON_CHOICES = (
    ("images/topic/icons/star.gif", "Star"),
    ("images/topic/icons/warning.gif", "Warning"),
    ("images/topic/icons/info.gif", "Info"),
    ("images/topic/icons/question.gif", "Question"),
    ("images/topic/icons/stop.gif", "Stop"),
    ("images/topic/icons/photo.gif", "Photo"),
)

# Create your models here.

class ForumGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    priority = models.IntegerField(unique=True)
    description = models.TextField()
    is_staff_group = models.BooleanField(default=False)
    is_messages_group = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    minimum_messages = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=10, default="#FFFFFF")
    icon = models.ImageField(null=True, blank=True, upload_to='images/group_icons/')

    class Meta:
        ordering = ['-priority']

    @property
    def get_absolute_url(self):
        return f"/groups/g{self.id}"

    def __str__(self):
        return self.name
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(null=True, blank=True, upload_to='images/profile_picture/')
    groups = models.ManyToManyField(ForumGroup, related_name='users')
    messages_count = models.IntegerField(default=0)
    desc = models.CharField(null=True, blank=True, max_length=20)
    localisation = models.CharField(null=True, blank=True, max_length=255)
    loisirs = models.CharField(null=True, blank=True, max_length=255)
    birthdate = models.DateTimeField()
    type = models.CharField(max_length = 20, choices = TYPE_CHOICES, default = "neutral") 
    favorite_games = models.CharField(null=True, blank=True, max_length=255)
    zodiac_sign = models.CharField(max_length = 20, choices = ZODIAC_CHOICES, null=True, blank=True)
    gender = models.CharField(max_length = 20, choices = GENDER_CHOICES)
    website = models.CharField(null=True, blank=True, max_length=255)
    skype = models.CharField(null=True, blank=True, max_length=255)
    signature = models.TextField(null=True, blank=True, max_length=65535)
    email_is_public = models.BooleanField(default=False)    
    last_login = models.DateTimeField(auto_now=True)
    name_color = models.CharField(max_length=20, null=True, blank=True, help_text="Color of the user's name in the forum. Use a hex color code starting with #.")
    top_group = models.ForeignKey(ForumGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='top_group_users', help_text="The top group of the user, used for displaying the user's group name and icon.")
    is_hidden = models.BooleanField(default=False)

    upload_size = models.BigIntegerField(default=0, help_text="Total upload size in bytes. Used for image upload limits.")

    def clean(self):
        super().clean() # Call parent's clean method
        if self.birthdate:
            # Define a reasonable minimum year (e.g., 1900 or 1)
            min_year = 1
            max_year = timezone.now().year
            if self.birthdate.year < min_year or self.birthdate.year > max_year:
                raise ValidationError({
                    'birthdate': f'Please enter a valid year between {min_year} and {max_year}.'
                })


    @property
    def get_top_group(self):
        if self.top_group:
            return self.top_group
        else:
            # If no top group is set, return the highest priority group
            # This assumes that groups are ordered by priority in descending order
            if self.groups.exists():
                # Get the first group ordered by priority
                top_group = self.groups.order_by('-priority').first()
                if top_group:
                    self.top_group = top_group
                    self.save()
                    return top_group
            return ForumGroup.objects.order_by('-priority').last()  # Return default group if none exists (lowest priority)

    @property
    def get_group_color(self):
        if self.top_group:
            return self.top_group.color
        if not self.name_color:
            top_group = self.get_top_group
            if top_group:
                self.name_color = top_group.color
                self.save()
                return top_group.color
            return "#FFFFFF"  # Default color if no group found
        else: # If name_color is set, return it
            return self.name_color
    
    @property
    def is_user_staff(self):
        return self.groups.filter(is_staff_group=True).exists()
    
    @property
    def get_user_age(self):
        """Get the user's age in years."""
        if self.birthdate and self.birthdate.year >= 1: # Check year again just in case
            today = timezone.now().date() # Compare with date part
            # Ensure birthdate is also treated as date for comparison
            bdate = self.birthdate.date()
            try:
                age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
                return age if age >= 0 else 0 # Return 0 if calculated age is negative
            except ValueError: # Catch potential errors if date parts are invalid (less likely now)
                return 0
        return 0
    
    @property
    def get_banner_color(self):
        """Get the user's banner color based on their type."""
        if self.type == "pacifist":
            return "#71DA71"
        elif self.type == "neutral":
            return "#9E9E9E"
        elif self.type == "genocide":
            return "#B41414"
        else:
            return "#9E9E9E"  # Default to neutral color if type is unknown

    def save(self, *args, **kwargs):
        # Check if is_hidden field has changed (for existing instances)
        is_hidden_changed = False
        old_is_hidden = None
        
        if self.pk is not None:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                old_is_hidden = old_instance.is_hidden
                is_hidden_changed = old_is_hidden != self.is_hidden
            except Profile.DoesNotExist:
                pass
        
        if self.pk is None:

            # Increment total_users for the forum if and only if this is a new profile
            try:
                UTF, _ = Forum.objects.get_or_create(name='UTF')
                UTF.total_users += 1
                UTF.save()
            except:
                print("ERROR : Forum UTF not found")


            # Save first, then mark all topics read for the user
            super().save(*args, **kwargs)
            mark_all_topics_read_for_user(self.user)
            
            # Make last_login the current time
            self.last_login = timezone.now()

        else:
            # Regular save for profile edits
            super().save(*args, **kwargs)
        
        if self.type == '':
            self.type = "neutral"
            
        # Handle is_hidden field changes
        if is_hidden_changed:
            self._handle_is_hidden_change(old_is_hidden, self.is_hidden)

        
    def _handle_is_hidden_change(self, old_value, new_value):
        """Handle actions when is_hidden field changes."""
        if old_value is False and new_value is True:
            # User became hidden
            print(f"User {self.user.username} became hidden")
            # TODO: [8] Clear latest_message references for topics where this user was the latest poster
            self._clear_latest_message_references()
            
        elif old_value is True and new_value is False:
            # User became visible
            print(f"User {self.user.username} became visible")
            # TODO: Update latest_message references for topics where this user should now be visible
            self._update_latest_message_references()
    
    def _clear_latest_message_references(self):
        """Clear latest_message references for topics where this user was the latest poster."""        
        # Find all topics where this user's posts are the latest_message
        topics_to_update = Topic.objects.filter(latest_message__author=self.user)
        
        for topic in topics_to_update:
            # Set latest_message to None to force recalculation
            topic.latest_message = None
            topic.save()
            
    def _update_latest_message_references(self):
        """Update latest_message references for topics where this user should now be visible."""
        # Find topics where this user has participated
        user_posts = Post.objects.filter(author=self.user).values('topic').distinct()
        topic_ids = [post['topic'] for post in user_posts]
        topics_to_update = Topic.objects.filter(id__in=topic_ids)
        
        for topic in topics_to_update:
            # Force recalculation of latest message
            topic.latest_message = None
            topic.save()
            # The get_latest_message property will recalculate the correct latest message
    
    def __str__(self):
        return f"{self.user}'s profile"
    

@receiver(m2m_changed, sender=Profile.groups.through)
def update_top_group_on_groups_change(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        if isinstance(instance, Profile):
            top_group = instance.groups.order_by('-priority').first()
            if instance.top_group != top_group:
                instance.top_group = top_group
                #print(f"Updated top group for {instance.user.username} to {top_group.name if top_group else 'None'}")
                instance.save(update_fields=['top_group'])


class Category(models.Model):
    name = models.CharField(max_length=60, default="DEFAULT_CATEGORY_NAME")
    slug = models.SlugField(max_length=255, blank=True)
    index_topics = models.ManyToManyField('Topic', related_name='index_topics', blank=True) 

    is_hidden = models.BooleanField(default = False)

    @property 
    def get_index_sub_forums(self):
        """THIS METHOD IS DEPRECATED AND SHOULD NOT BE USED"""
        return Topic.objects.filter(category=self, is_index_topic=True)
    
    @property 
    def get_absolute_url(self):
        return f"/c{self.id}-{self.slug}"

    
    def save(self, *args, **kwargs):
        
        if not self.slug or self.slug == "":
            self.slug = slugify(self.title)
            if not self.slug: #if the title is not slugifiable, like "?????"
                self.slug = "category" #str(uuid.uuid4())[:8]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
    

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="replies", null=True, blank=True)
    text = models.TextField(max_length=65535, default="DEFAULT POST TEXT")
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    update_count = models.IntegerField(default=0, null=True)

    @property
    def get_page_number(self):
        """Get the page number of this post in the topic."""
        if self.topic:
            # Get all posts in the topic, ordered by created time
            posts = list(self.topic.replies.all().order_by('created_time'))
            # Find the index of this post in the list
            index = posts.index(self)
            # Calculate the page number (1-based)
            page_number = (index // 15) + 1
            return page_number
        return None
    
    @property
    def get_relative_id(self):
        """Get the relative ID of this post in the topic."""
        if self.topic:
            # Get all posts in the topic, ordered by created time
            posts = list(self.topic.replies.all().order_by('created_time'))
            # Find the index of this post in the list
            index = posts.index(self)
            # Return the relative ID (1-based)
            return index + 1
        return None
    
    @property
    def get_raw_text(self):
        """Get the raw text of this post, without bbcode tags using the strip_bbcode function, and shortens it."""
        # Use the strip_bbcode function to remove BBCode tags
        return strip_bbcode(self.text)

    def save(self, *args, **kwargs):

        # If this is a new post
        if self.pk is None:
            print(f"New post {self} created")

            # Increment total_messages for the forum
            try:
                UTF, _ = Forum.objects.get_or_create(name='UTF')
                UTF.total_messages += 1
                UTF.save()
            except Exception as e:
                print(f"ERROR : Forum UTF not found ({e})")

            # Increment message count for author's profile
            if self.author:
                if self.author.profile:
                    self.author.profile.messages_count += 1
                    self.author.profile.save()
                    print(f"Message count for {self.author} incremented to {self.author.profile.messages_count}")

            # # Update latest message time for the topic
            # if self.topic:
            #     latest_message = self.topic.get_latest_message
            #     if latest_message:
            #         self.topic.last_message_time = timezone.now() # this is ugly and should be fixed with a signal or something
            #         self.topic.save()
            #         print(f"Latest message time for {self.topic} updated to {self.topic.last_message_time}")
            #     else:
            #         print("No messages found")

            # Increment total_replies for all ancestor topics and the topic itself
            if self.topic:
                current = self.topic
                while current.parent is not None:
                    current.total_replies += 1
                    current.save()
                    print(f"Total replies for {current} incremented to {current.total_replies}")
                    current = current.parent
                current.total_replies += 1
                current.save()

            # Check if author now has enough messages to be promoted to a new group
            if self.author:
                if self.author.profile:
                    # Exclude groups that the user is already in
                    user_groups = self.author.profile.groups.all()
                    for group in ForumGroup.objects.filter(is_messages_group=True).exclude(id__in=user_groups).order_by('-priority'):
                        if self.author.profile.messages_count >= group.minimum_messages:
                            self.author.profile.groups.add(group)
                            self.author.profile.name_color = group.color if group.color else "#FFFFFF"  # Set the name color to the group's color
                            self.author.profile.save()
                            print(f"{self.author} promoted to {group} with color {group.color}")

            # Update the topic's latest message
            super().save(*args, **kwargs) # Save the post first
            current_topic = self.topic
            counter = 0
            while current_topic:
                # Update the topic's latest message to this post
                current_topic.latest_message = self
                current_topic.last_message_time = self.created_time
                current_topic.save()
                print(f"Latest message for {current_topic} updated to {self} at {self.created_time} (pass {counter})")
                # Update the parents subforums as well
                current_topic = current_topic.parent
                counter += 1

        # If this is an edit
        else:
            print(f"Post {self} edited")
            self.update_count += 1
            super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.author}'s reply on {self.topic}"

class Topic(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="topics", null=True, blank=True)
    title = models.CharField(max_length=60, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    icon = models.CharField(null=True, blank=True, max_length=60)
    slug = models.SlugField(max_length=255, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    latest_message = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_latest_message')
    last_message_time = models.DateTimeField(auto_now_add=True, null=True)
    total_children = models.IntegerField(default=0) #only applicable to sub forums
    total_replies = models.IntegerField(default=-1) #minus 1 because the first post is not counted as a reply
    total_views = models.IntegerField(default=0)

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    is_sub_forum = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    is_index_topic = models.BooleanField(default=False)
    has_subforum_children = models.BooleanField(default=False)
    
    @property
    def is_root_topic(self):
        return self.parent == None
    
    @property
    def get_latest_message(self):
        if self.latest_message and self.latest_message.author and not self.latest_message.author.profile.is_hidden: 
            # If latest message is hidden, fetch again and update
            # But, if a user is the author of the latest message, and they go hidden, and then unhide, the latest message should now be theirs... But it won't update right away
            # TODO: [8] Make sure that when a user hides or unhides, all the topics they participated in get their latest_message set to NULL.
            return self.latest_message
        else:
            if self.is_sub_forum:
                # Collect all descendant topics including self using BFS
                all_topics = []
                queue = deque([self])

                while queue:
                    current_topic = queue.popleft()
                    all_topics.append(current_topic)
                    queue.extend(current_topic.children.all())

                # Get the latest post from all collected topics
                latest_post = Post.objects.filter(topic__in=all_topics, author__profile__is_hidden=False).order_by('-created_time').first()
                self.latest_message = latest_post
                self.save() # Save the topic to update the latest_message field
                return latest_post
            
            else:
                latest_post = Post.objects.filter(topic=self, author__profile__is_hidden=False).order_by('-created_time').first()
                self.latest_message = latest_post
                self.save() # Save the topic to update the latest_message field
                return latest_post
    
    @property
    def get_tree(self):
        """Get the tree of topics starting from its parent, then its parent's parent, and stop at the root topic."""
        tree = {}
        if self.is_sub_forum: # this is because xooit is weird and the tree structure is different for sub forums, they include themselves in the tree but not the topics
            current = self
        else:
            current = self.parent
        while current:
            if current not in tree:
                tree[current] = []
            if current.parent:
                if current.parent not in tree:
                    tree[current.parent] = [current]
                else:
                    tree[current.parent].append(current)
            current = current.parent
        return {parent: children for parent, children in reversed(tree.items())} # Reverse the tree so that the root topic is at the left
    
    @property
    def get_absolute_url(self):
        if self.is_sub_forum:
            return f"/f{self.id}-{self.slug}"
        else:
            return f"/t{self.id}-{self.slug}"
        
    @property
    def get_sub_forums(self):
        if self.is_sub_forum and self.has_subforum_children:
            # Return all direct children that are sub forums
            return self.children.filter(is_sub_forum=True)
        else:
            return Topic.objects.none()  # Return an empty queryset if not a sub forum or no children
    
    @property
    def get_depth(self):
        """Get the depth of this topic in the tree."""
        depth = 0
        current = self
        while current.parent:
            depth += 1
            current = current.parent
        return depth
    
    @property
    def get_max_page(self):
        """Get the maximum page number for this topic."""
        if self.total_replies <= 0:
            return 1
        else:
            return (self.total_replies // 15) + 1
        
    @property
    def get_page_numbers_subforum_details(self):
        """Get the list of page numbers for this topic.
        If there are many pages, display first page, ellipsis, and last 3 pages.
        """
        max_page = self.get_max_page
        if max_page <= 4:
            return list(range(1, max_page + 1))
        else:
            return [1, '...'] + list(range(max_page - 2, max_page + 1))
        
    @property
    def get_first_post(self):
        """Get the first post of this topic."""
        first_post = Post.objects.filter(topic=self).order_by('created_time').first()
        return first_post
        
    def check_subforum_unread(subforum, user):
        """ Check if any child topic in a subforum is unread by the user.
            THIS METHOD IS DEPRECATED AND SHOULD NOT BE USED ANYMORE"""
        if not user.is_authenticated:
            return False

        # Get all direct child topics of this subforum
        child_topics = subforum.children.all()

        # Get read statuses for these topics in bulk
        read_statuses = TopicReadStatus.objects.filter(user=user,topic__in=child_topics).values('topic_id', 'last_read')

        # Build a lookup dictionary {topic_id: last_read_time}
        read_status_map = {rs['topic_id']: rs['last_read'] for rs in read_statuses}

        # Check each child topic
        for topic in child_topics:
            last_read = read_status_map.get(topic.id)
            if not last_read:  # Never read
                return True
            if topic.last_message_time > last_read:
                return True

        return False
    
    def clean(self):

        if self.parent != None:
            if self.parent.is_sub_forum == False:
                raise ValidationError("The parent of this topic is not a sub forum.")
        

    def save(self, *args, **kwargs):

        if not self.slug or self.slug == "":
            self.slug = slugify(self.title)
            if not self.slug: #if the title is not slugifiable, like "?????"
                self.slug = "topic" #str(uuid.uuid4())[:8]

        # Sync category with parent's category if parent exists
        if self.parent:
            if not self.parent.category:
                raise ValidationError("Parent topic must have a category.")
            if not self.category:
                self.category = self.parent.category

        if self.pk is None: # If this is a new topic
            if self.parent:   # Increment parent's children count when new topic is created (total_replies will be handled by the Post's save method)
                self.parent.total_children += 1
                self.parent.save()

            if self.is_sub_forum: # Make total replies 0 instead of -1
                self.total_replies = 0
                if self.parent and not self.parent.has_subforum_children: # If this is a sub forum, we need to set the parent as having subforum children
                    print(f"Setting parent {self.parent} as having subforum children")
                    self.parent.has_subforum_children = True
                    self.parent.save()

            self.created_time = timezone.now()
            self.last_message_time = timezone.now()
        
        super().save(*args, **kwargs)
        
        # After saving, sync this with index_topics of the category
        if self.is_index_topic == True:
            self.category.index_topics.add(self)

        if self.is_announcement:
            utf = Forum.objects.get(name='UTF')
            utf.announcement_topics.add(self)


    def __str__(self):
        if self.is_sub_forum:
            return f"[SUBFORUM] {self.title} by {self.author}"
        else:
            if self.parent: 
                return f"(In {self.parent.title}) {self.title} by {self.author}"
            else:
                return f"{self.title} by {self.author}"


class Forum(models.Model):
    name = models.CharField(max_length=20)
    announcement_topics = models.ManyToManyField(Topic, blank=True)
    total_users = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    online_record = models.IntegerField(default=0)
    online_record_date = models.DateTimeField(auto_now_add=True)

    @property
    def get_announcement_topics(self):
        if self.annoucement_topics.count() == 0:
            self.annoucement_topics = Topic.objects.filter(is_annoucement=True)
        else:
            return self.annoucement_topics
        
    @property
    def get_latest_user(self):
        # Returns the user object of the user with the latest creation date which has a profile associated with it
        return User.objects.filter(profile__isnull=False).order_by('-date_joined').first()
    
    @property
    def get_total_topics(self):
        """Get the total number of topics in this forum."""
        return Topic.objects.filter(is_sub_forum=False).count()

    def __str__(self):
        return self.name
    

class TopicReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    last_read = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user} last read {self.topic} at {self.last_read}"
    





class SmileyCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    smileys = models.ManyToManyField(SmileyTag, related_name='categories', blank=True)

    def __str__(self):
        return self.name
    




class Poll(models.Model):
    topic = models.OneToOneField(
        'Topic',
        on_delete=models.CASCADE,
        related_name='poll',
    )
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Max number of options a user can choose. -1 for unlimited.
    max_choices_per_user = models.IntegerField(default=1)
    
    # Number of days voting is open. -1 for no limit.
    days_to_vote = models.IntegerField(default=-1)

    can_change_vote = models.IntegerField(default=1)

    @property
    def is_active(self) -> bool:
        """Checks if the poll is currently active for voting."""
        if self.days_to_vote <= 0: # Typically 0 or -1
            return True  # No time limit
        # auto_now_add=True ensures created_at is set on creation.
        if not self.created_at:
            return False # Should not happen if saved to DB
        deadline = self.created_at + datetime.timedelta(days=self.days_to_vote)
        return timezone.now() <= deadline
      
    @property 
    def get_total_vote_count(self) -> int:
        aggregation = self.options.annotate(
            num_voters_for_option=Count('voters')
        ).aggregate(
            total_poll_votes=Sum('num_voters_for_option')
        )
        return aggregation['total_poll_votes'] or 0
    
    @property
    def allow_multiple_choices(self) -> bool:
        """Checks if the poll allows multiple choices."""
        return self.max_choices_per_user != 1

    def get_user_vote_count(self, user: User) -> int:
        """Counts how many distinct options the given user has voted for in this poll."""
        if not user or not user.is_authenticated:
            return 0
        # self.options comes from PollOption.poll's related_name='options'
        return self.options.filter(voters=user).count()

    def can_user_cast_new_vote(self, user: User) -> bool:
        """
        Checks if the user can cast a new (additional) vote in this poll.
        This means the poll is active and the user has not yet reached their maximum allowed number of choices.
        This method does NOT check if the user has already voted for a *specific option* they might be trying to vote on right now.
        """
        if not self.is_active:
            return False
        
        if self.max_choices_per_user == -1:  # Unlimited choices allowed
            return True
        
        current_user_votes = self.get_user_vote_count(user)
        return current_user_votes < self.max_choices_per_user
    
    def has_user_voted(self, user: User) -> bool:
        """
        Checks if the given user has voted for at least one option in this poll.
        """
        if not user or not user.is_authenticated:
            return False
        # self.options is the reverse relation from PollOption.poll
        # We filter these options to see if any of them have the user in their 'voters' M2M field.
        # .exists() is efficient as it translates to an SQL EXISTS query.
        return self.options.filter(voters=user).exists()

    def __str__(self):
        topic_title = "N/A"
        try:
            if self.topic_id and self.topic: # Check topic_id first to avoid query if it's None
                topic_title = self.topic.title
        except Topic.DoesNotExist:
            # This case should ideally not be reached if on_delete=CASCADE works
            # and topic_id is always valid or poll is deleted.
            pass 
            
        return f"Poll: {self.question} (For Topic: {topic_title})"

    class Meta:
        ordering = ['-created_at']


class PollOption(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='options', # Allows poll_instance.options.all()
    )
    text = models.CharField(max_length=255)

    voters = models.ManyToManyField(
        User,
        related_name='poll_votes', # user_instance.poll_votes.all() gets all options voted by a user
        blank=True, # An option can have zero votes; a user does not have to vote.
    )

    @property
    def get_vote_count(self) -> int:
        """Returns the number of votes this option has received."""
        return self.voters.count()
    
    @property
    def get_percentage(self) -> int:
        """Returns the percentage of votes based on total votes in the poll."""
        total_poll_votes = self.poll.get_total_vote_count
        if not total_poll_votes:  # Handles case where total_poll_votes is 0 or None
            return 0
        
        option_vote_count = self.get_vote_count
        if option_vote_count is None: # Should not happen with .count()
            return 0

        return int((option_vote_count / total_poll_votes) * 100)
    
    @property
    def get_bar_length(self) -> int:
        """Returns width in pixels for the bar in the frontend.
        The calculation is the following: 2*percentage + (5% of 2*percentage, floored)"""
        percentage = self.get_percentage
        if percentage == 0:
            return 0

        bar_length = int(2 * percentage + (0.05 * 2 * percentage))
        return bar_length

    def __str__(self):
        poll_question_snippet = "N/A"
        try:
            if self.poll_id and self.poll:
                poll_question_snippet = self.poll.question[:30] + ("..." if len(self.poll.question) > 30 else "")
        except Poll.DoesNotExist:
             pass
        return f"Option: {self.text} (For Poll: {poll_question_snippet})"

    class Meta:
        # Ensures option text is unique within a specific poll.
        #unique_together = ('poll', 'text')
        ordering = ['id'] 

class Subforum(models.Model):
    parent = models.ManyToManyField(Topic, related_name='subforums', blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_hidden = models.BooleanField(default=False)

    @property
    def get_absolute_url(self):
        return f"/f{self.topic.id}-{self.topic.slug}"

    def __str__(self):
        return f"Subforum: {self.topic.title} (ID: {self.topic.id})"
    

class PrivateMessageThread(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pm_threads_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pm_threads_received')
    title = models.CharField(max_length=255, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PM Thread: {self.title} by {self.author.username} to {self.recipient.username}"

    class Meta:
        ordering = ['id']
    

class PrivateMessage(models.Model):
    thread = models.ForeignKey(PrivateMessageThread, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pm_messages_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pm_messages_received')
    text = models.TextField(max_length=65535)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    @property
    def get_relative_id(self): # It's recommend to do select_related(thread__messages) on the query to avoid N+1 queries.
        relative_id = self.thread.messages.filter(created_time__lte=self.created_time).count()
        return relative_id
        
    def __str__(self):
        return f"Response {self.get_relative_id} by {self.author.username} to {self.recipient.username} in PM Thread: {self.thread.title}"
    
    class Meta:
        ordering = ['id']