# archive/models.py

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

class ArchiveSafeDateTimeField(models.DateTimeField):
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
    return

    # # Circular import avoided by using local reference
    # from .models import ArchiveTopic, ArchiveTopicReadStatus
    
    # # Get all topics in the forum
    # all_topics = ArchiveTopic.objects.all()

    # # Iterate through each topic and mark it as read for the user
    # for topic in all_topics:
    #     ArchiveTopicReadStatus.objects.update_or_create(
    #         user=user,
    #         topic=topic,
    #         defaults={'last_read': timezone.now()}
    #     )

# Choices for CharField(choices = ...)

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
        'code', 'center'
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


# Start of archive models

class FakeUser(models.Model):
    """
    A fake user model to allow for the creation of profiles without a real user, because they won't need passwords.
    This is useful for creating archive users as they are hardcoded. They also won't clash with the real User model.
    This model is not intended for use in the actual forum app.
    """
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=15000, null=True, blank=True)
    email = models.CharField(max_length=15000, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_authenticated = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class ArchiveForumGroup(models.Model):
    name = models.CharField(max_length=5000, unique=True)
    priority = models.IntegerField(unique=True)
    description = models.TextField()
    is_staff_group = models.BooleanField(default=False)
    is_messages_group = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    minimum_messages = models.IntegerField()
    created_at = models.DateTimeField()
    color = models.CharField(max_length=1000, default="#FFFFFF")
    icon = models.ImageField(null=True, blank=True, upload_to='images/group_icons/')

    class Meta:
        ordering = ['-priority']

    @property
    def get_absolute_url(self):
        return f"/archive/groups/g{self.id}"

    def __str__(self):
        return self.name
    

class ArchiveProfile(models.Model):
    user = models.OneToOneField(FakeUser, on_delete=models.CASCADE, db_constraint=False)
    profile_picture = models.CharField(null=True, blank=True, max_length=25500) # This should be a URL or path to the profile picture, for easier management (e.g. /media/images/profile_picture/username.jpg)
    groups = models.ManyToManyField('ArchiveForumGroup', related_name='archive_users')
    messages_count = models.IntegerField(default=0)
    desc = models.CharField(null=True, blank=True, max_length=2000)
    localisation = models.CharField(null=True, blank=True, max_length=25500)
    loisirs = models.CharField(null=True, blank=True, max_length=25500)
    birthdate = models.DateTimeField()
    type = models.CharField(max_length = 20, choices = TYPE_CHOICES, default = "neutral", null=True) 
    favorite_games = models.CharField(null=True, blank=True, max_length=25500)
    zodiac_sign = models.CharField(max_length = 20, choices = ZODIAC_CHOICES, null=True, blank=True)
    gender = models.CharField(max_length = 20, choices = GENDER_CHOICES, null=True)
    website = models.CharField(null=True, blank=True, max_length=25500)
    skype = models.CharField(null=True, blank=True, max_length=25500)
    signature = models.TextField(null=True, blank=True, max_length=6553500)
    email_is_public = models.BooleanField(default=False)    
    last_login = models.DateTimeField()
    name_color = models.CharField(max_length=20, null=True, blank=True, help_text="Color of the user's name in the forum. Use a hex color code starting with #.")
    top_group = models.ForeignKey(ArchiveForumGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='top_group_users', help_text="The top group of the user, used for displaying the user's group name and icon.")

    upload_size = models.BigIntegerField(default=0, help_text="Total upload size in bytes. Used for image upload limits.")

    is_hidden = models.BooleanField(default=False)
    display_id = models.IntegerField(default=0) # Warning: This is not the actual ID, but a display ID for the profile, used in the memberlist view.
    display_username = models.CharField(null=True, blank=True, max_length=25500)

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
            return ArchiveForumGroup.objects.order_by('-priority').last()  # Return default group if none exists (lowest priority)
    
    @property
    def get_group_color(self):
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
            today = (timezone.now() + datetime.timedelta(days=30)).date() # Use a future date because it's only used to display the age after birthday
            # Ensure birthdate is also treated as date for comparison
            bdate = self.birthdate.date()
            try:
                age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
                return age if age >= 0 else 0 # Return 0 if calculated age is negative
            except ValueError: # Catch potential errors if date parts are invalid (less likely now)
                return 0
        return 0
    
    def get_user_age_past(self, before_datetime=None):
        """Get the user's age in years, considering a past date."""
        if self.birthdate and self.birthdate.year >= 1: # Check year again just in case
            today = (before_datetime + datetime.timedelta(days=30)).date() # Use a future date because it's only used to display the age after birthday
            # Ensure birthdate is also treated as date for comparison
            bdate = self.birthdate.date()
            try:
                age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
                return age if age >= 0 else 0 # Return 0 if calculated age is negative
            except ValueError: # Catch potential errors if date parts are invalid (less likely now)
                return 0
        return 0
    
    @property
    def get_avatar_url(self):
        if self.profile_picture:
            return f"/media/archive/{self.profile_picture}"
        return None
    
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

        
        if self.pk is None:

            # Increment total_users for the forum if and only if this is a new profile
            try:
                UTF, _ = ArchiveForum.objects.get_or_create(name='UTF')
                UTF.total_users += 1
                UTF.save()
            except:
                #print("ERROR : Forum UTF not found")
                pass


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

        
    
    def __str__(self):
        return f"{self.user}'s profile"


@receiver(m2m_changed, sender=ArchiveProfile.groups.through)
def update_top_group_on_groups_change(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        if isinstance(instance, ArchiveProfile):
            top_group = instance.groups.order_by('-priority').first()
            if instance.top_group != top_group:
                instance.top_group = top_group
                #print(f"Updated top group for {instance.user.username} to {top_group.name if top_group else 'None'}")
                instance.save(update_fields=['top_group'])


class ArchiveCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=6000, default="DEFAULT_CATEGORY_NAME")
    slug = models.SlugField(max_length=25500, blank=True)
    index_topics = models.ManyToManyField('ArchiveTopic', related_name='archive_index_topics', blank=True) 

    is_hidden = models.BooleanField(default = False)

    @property 
    def get_index_sub_forums(self):
        """THIS METHOD IS DEPRECATED AND SHOULD NOT BE USED"""
        return ArchiveTopic.objects.filter(category=self, is_index_topic=True)
    
    @property 
    def get_absolute_url(self):
        return f"/archive/c{self.id}-{self.slug}"
    
    @property
    def get_all_topics(self):
        """Get all topics in this category, including non-root topics."""
        return ArchiveTopic.objects.filter(category=self)
    
    @property
    def get_root_topics(self):
        """Get all root topics in this category, including root non-index topics."""
        return ArchiveTopic.objects.filter(category=self, parent=None)
    
    @property
    def get_all_subforums(self):
        """Get all subforums in this category."""
        return ArchiveTopic.objects.filter(category=self, is_sub_forum=True)
    
    @property
    def get_all_index_topics(self):
        """Get all index topics in this category."""
        return self.index_topics.all()
    
    def save(self, *args, **kwargs):
        
        if not self.slug or self.slug == "":
            self.slug = slugify(self.name)
            if not self.slug: #if the name is not slugifiable, like "?????"
                self.slug = "category" #str(uuid.uuid4())[:8]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
    

class ArchivePost(models.Model):
    id = models.IntegerField(primary_key=True)
    author = models.ForeignKey(FakeUser, on_delete=models.SET_NULL, related_name="archive_posts", null=True, blank=True, db_constraint=False)
    topic = models.ForeignKey('ArchiveTopic', on_delete=models.CASCADE, related_name="archive_replies", null=True, blank=True)
    text = models.TextField(max_length=6553500, default="DEFAULT POST TEXT")
    created_time = models.DateTimeField()
    updated_time = models.DateTimeField(null=True, blank=True)
    update_count = models.IntegerField(default=0, null=True)

    @property
    def get_page_number(self):
        """Get the page number of this post in the topic."""
        if self.topic:
            # Get all posts in the topic, ordered by created time
            posts = list(self.topic.archive_replies.all().order_by('created_time'))
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
            posts = list(self.topic.archive_replies.all().order_by('created_time'))
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
    
    @property
    def get_absolute_url(self):
        return f"/archive/p{self.id}"

    def save(self, *args, **kwargs):

        # If this is a new post
        if self.pk is None:
            #print(f"New post {self} created")

            # Increment total_messages for the forum
            try:
                UTF, _ = ArchiveForum.objects.get_or_create(name='UTF')
                UTF.total_messages += 1
                UTF.save()
            except Exception as e:
                #print(f"ERROR : Forum UTF not found ({e})")
                pass

            # Increment message count for author's profile
            if self.author:
                if hasattr(self.author, 'archiveprofile'):
                    self.author.archiveprofile.messages_count += 1
                    self.author.archiveprofile.save()
                    #print(f"Message count for {self.author} incremented to {self.author.archiveprofile.messages_count}")

            # Update latest message time for the topic
            # if self.topic:
            #     latest_message = self.topic.get_latest_message
            #     if latest_message:
            #         self.topic.last_message_time = timezone.now() # this is ugly and should be fixed with a signal or something
            #         self.topic.save()
            #         #print(f"Latest message time for {self.topic} updated to {self.topic.last_message_time}")
            #     else:
            #         #print("No messages found")
            #         pass

            # Increment total_replies for all ancestor topics and the topic itself
            if self.topic:
                current = self.topic
                while current.parent is not None:
                    current.total_replies += 1
                    current.save()
                    #print(f"Total replies for {current} incremented to {current.total_replies}")
                    current = current.parent
                current.total_replies += 1
                current.save()

            # Check if author now has enough messages to be promoted to a new group
            if self.author:
                if hasattr(self.author, 'archiveprofile'):
                    # Exclude groups that the user is already in
                    user_groups = self.author.archiveprofile.groups.all()
                    for group in ArchiveForumGroup.objects.filter(is_messages_group=True).exclude(id__in=user_groups).order_by('-priority'):
                        if self.author.archiveprofile.messages_count >= group.minimum_messages:
                            self.author.archiveprofile.groups.add(group)
                            self.author.archiveprofile.save()
                            #print(f"{self.author} promoted to {group}")

            # Update the topic's latest message
            super().save(*args, **kwargs) # Save the post first
            current_topic = self.topic
            counter = 1
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
            # print(f"Post {self} edited")
            # self.update_count += 1
            1+1
            super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.author}'s reply on {self.topic}"

class ArchiveTopic(models.Model):
    id = models.IntegerField(primary_key=True)
    author = models.ForeignKey(FakeUser, on_delete=models.SET_NULL, related_name="archive_topics", null=True, blank=True, db_constraint=False)
    title = models.CharField(max_length=6000, null=True, blank=True)
    description = models.CharField(max_length=25500, null=True, blank=True)
    icon = models.CharField(null=True, blank=True, max_length=6000)
    slug = models.SlugField(max_length=25500, blank=True)
    created_time = models.DateTimeField()
    latest_message = models.ForeignKey(ArchivePost, on_delete=models.SET_NULL, null=True, blank=True, related_name='archive_related_latest_message')
    last_message_time = models.DateTimeField(null=True)
    total_children = models.IntegerField(default=0) #only applicable to sub forums
    total_replies = models.IntegerField(default=-1) #minus 1 because the first post is not counted as a reply
    total_views = models.IntegerField(default=0)

    category = models.ForeignKey('ArchiveCategory', on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='archive_children')

    is_sub_forum = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    is_index_topic = models.BooleanField(default=False)
    has_subforum_children = models.BooleanField(default=False) # This is used to determine if the topic has subforums, not children topics
    moved = models.BooleanField(default=False)

    # For archives

    display_id = models.IntegerField(default=0) #for display purposes (in the url of subforums), not the actual ID
    display_children = models.IntegerField(default=0) #only applicable to sub forums
    display_replies = models.IntegerField(default=-1) #minus 1 because the first post is not counted as a reply
    display_views = models.IntegerField(default=0)

    
    @property
    def is_root_topic(self):
        return self.parent == None
    
    @property
    def get_latest_message(self):
        if self.latest_message:
            return self.latest_message
        else:
            if self.is_sub_forum:
                # Collect all descendant topics including self using BFS
                all_topics = []
                queue = deque([self])

                while queue:
                    current_topic = queue.popleft()
                    all_topics.append(current_topic)
                    queue.extend(current_topic.archive_children.all())

                # Get the latest post from all collected topics
                latest_post = ArchivePost.objects.filter(topic__in=all_topics).order_by('-created_time').first()
                self.latest_message = latest_post
                self.save() # Save the topic to update the latest_message field
                return latest_post
        
            else:
                latest_post = ArchivePost.objects.filter(topic=self).order_by('-created_time').first()
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
            return f"/archive/f{self.display_id}-{self.slug}"
        else:
            return f"/archive/t{self.id}-{self.slug}"
        
    @property
    def get_sub_forums(self):
        #print(f"Sub forums for {self}: {self.archive_children.all()}")
        if self.is_sub_forum and self.has_subforum_children:
            # Return all direct children that are sub forums
            return self.archive_children.filter(is_sub_forum=True)
        else:
            return ArchiveTopic.objects.none()  # Return an empty queryset if not a sub forum or no children
    
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
        if self.display_replies <= 0:
            return 1
        else:
            return (self.display_replies // 15) + 1
        
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
        first_post = ArchivePost.objects.filter(topic=self).order_by('created_time').first()
        return first_post
        
    def check_subforum_unread(subforum, user):
        return False
        # """ Check if any child topic in a subforum is unread by the user.
        #     THIS METHOD IS DEPRECATED AND SHOULD NOT BE USED ANYMORE"""

        # # Get all direct child topics of this subforum
        # child_topics = subforum.children.all()

        # # Get read statuses for these topics in bulk
        # read_statuses = ArchiveTopicReadStatus.objects.filter(user=user,topic__in=child_topics).values('topic_id', 'last_read')

        # # Build a lookup dictionary {topic_id: last_read_time}
        # read_status_map = {rs['topic_id']: rs['last_read'] for rs in read_statuses}

        # # Check each child topic
        # for topic in child_topics:
        #     last_read = read_status_map.get(topic.id)
        #     if not last_read:  # Never read
        #         return True
        #     if topic.last_message_time > last_read:
        #         return True

        # return False

    def get_latest_message_before(self, before_datetime=None):
        """Get the latest message in this topic before a given date."""
        if self.is_sub_forum:
            # Collect all descendant topics including self using BFS
            all_topics = []
            queue = deque([self])

            while queue:
                current_topic = queue.popleft()
                all_topics.append(current_topic)
                queue.extend(current_topic.archive_children.all())

            # Get the latest post from all collected topics
            latest_post = ArchivePost.objects.filter(topic__in=all_topics, created_time__lte=before_datetime).order_by('-created_time').first()
            return latest_post
        
        else:
            latest_post = ArchivePost.objects.filter(topic=self, created_time__lte=before_datetime).order_by('-created_time').first()
            return latest_post
        
    @property
    def get_past_page_numbers(self):
        """Get the list of page numbers for this topic, considering "past_total_replies" field.
        I don't know if an annotation would be better, might need to test it."""
        if self.past_total_replies <= 0 or not self.past_total_replies:
            #print(f"[Topic {self}] No past replies, returning page 1")
            return [1]
        else:
            #print(f"[Topic {self}] Has {self.past_total_replies} past replies, calculating page numbers")
            # Calculate the maximum page number based on replies
            max_page = (self.past_total_replies // 15) + 1
            if max_page <= 4:
                #print(f"[Topic {self}] Max page is {max_page}, returning all pages")
                return list(range(1, max_page + 1))
            else:
                #print(f"[Topic {self}] Max page is {max_page}, returning first page, ellipsis, and last 3 pages")
                return [1, '...'] + list(range(max_page - 2, max_page + 1))
            
    def get_past_views(self, fake_datetime, past_total_replies):
        print(f"{self} - Getting past views with fake_datetime={fake_datetime} and past_total_replies={past_total_replies}")
        """Get the past views of this post."""
        if not fake_datetime or past_total_replies == None:
            print(f"Attribute error for {self}")
            return self.display_views
        if self.display_replies == 0:
            print(f"Total replies is 0 for {self}, returning display views")
            return self.display_views
        print(f"Calculating following expression : ({past_total_replies} / {self.display_replies}) * {self.display_views}")
        return int((past_total_replies / self.display_replies) * self.display_views)

    def clean(self):
        if self.parent != None:
            if self.parent.is_sub_forum == False:
                raise ValidationError("The parent of this topic is not a sub forum.")
        

    def save(self, *args, **kwargs):

        if not self.slug and self.title:
            self.slug = slugify(self.title)

        # Sync category with parent's category if parent exists
        if self.parent:
            if not self.parent.category:
                raise ValidationError("Parent topic must have a category.")
            if not self.category:
                self.category = self.parent.category

        if self.pk is None: # If this is a new topic
            if self.parent:   # Increment parent's children count when new topic is created (total_replies will be handled by the ArchivePost's save method)
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
        
        if not self.slug:
            self.slug = str(self.id)
            super().save(update_fields=['slug'])

        # After saving, sync this with index_topics of the category
        if self.is_index_topic and self.category:
            self.category.index_topics.add(self)

        if self.is_announcement:
            utf, _ = ArchiveForum.objects.get_or_create(name='UTF')
            utf.announcement_topics.add(self)


    def __str__(self):
        if self.is_sub_forum:
            return f"[SUBFORUM] {self.title} by {self.author}"
        else:
            if self.parent: 
                return f"(In {self.parent.title}) {self.title} by {self.author}"
            else:
                return f"{self.title} by {self.author}"


class ArchiveForum(models.Model):
    name = models.CharField(max_length=2000)
    announcement_topics = models.ManyToManyField('ArchiveTopic', blank=True, related_name="archive_announcement_topics")
    total_users = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    online_record = models.IntegerField(default=0)
    online_record_date = models.DateTimeField()

    @property
    def get_announcement_topics(self):
        if self.announcement_topics.count() == 0:
            self.announcement_topics = ArchiveTopic.objects.filter(is_announcement=True)
        else:
            return self.announcement_topics
        
    @property
    def get_latest_user(self):
        # Returns the user object of the user with the latest creation date which has a profile associated with it
        latest_user = FakeUser.objects.filter(archiveprofile__isnull=False).order_by('-date_joined').first()
        return latest_user if latest_user else None
    
    @property
    def get_total_topics(self):
        """Get the total number of topics in this forum."""
        return ArchiveTopic.objects.count()

        
    def __str__(self):
        return self.name
    

class ArchiveTopicReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_constraint=False)
    topic = models.ForeignKey('ArchiveTopic', on_delete=models.CASCADE)
    last_read = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user} last read {self.topic} at {self.last_read}"
    





class ArchiveSmileyCategory(models.Model):
    name = models.CharField(max_length=5000, unique=True)
    smileys = models.ManyToManyField(
        # Using the string 'app_label.ModelName' for models in other apps
        # or for forward references to models not yet defined in the same file.
        'precise_bbcode.SmileyTag',
        through='ArchiveSmileyCategory_smileys', # Specifies the custom intermediate model
        related_name='archive_categories',
        blank=True  # Corresponds to blank=True in the AddField operation
    )

    def __str__(self):
        return self.name

    class Meta:
        # Optional: if you want more descriptive names in Django admin
        # verbose_name = "Archive Smiley Category"
        # verbose_name_plural = "Archive Smiley Categories"
        pass


class ArchiveSmileyCategory_smileys(models.Model):
    # This is the custom "through" model for the ManyToMany relationship
    # between ArchiveSmileyCategory and SmileyTag.

    archivesmileycategory = models.ForeignKey(
        ArchiveSmileyCategory,
        on_delete=models.CASCADE
    )
    smileytag = models.ForeignKey(
        'precise_bbcode.SmileyTag', # Again, string reference
        on_delete=models.CASCADE,
        db_constraint=False  # This was specified in the migration
    )

    class Meta:
        # This unique_together constraint was specified in the migration options
        unique_together = ('archivesmileycategory', 'smileytag')
        # Optional: if you want more descriptive names in Django admin
        # verbose_name = "Archive Smiley Category - Smiley Link"
        # verbose_name_plural = "Archive Smiley Category - Smiley Links"

    def __str__(self):
        return f"{self.archivesmileycategory.name} - {self.smileytag}"
    




class ArchivePoll(models.Model):
    topic = models.OneToOneField(
        'ArchiveTopic',
        on_delete=models.CASCADE,
        related_name='archive_poll',
    )
    question = models.CharField(max_length=25500)
    created_at = models.DateTimeField()
    
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
        aggregation = self.archive_options.annotate(
            num_voters_for_option=Count('voters')
        ).aggregate(
            total_poll_votes=Sum('num_voters_for_option')
        )
        return aggregation['total_poll_votes'] or 0
    
    @property
    def allow_multiple_choices(self) -> bool:
        """Checks if the poll allows multiple choices."""
        return self.max_choices_per_user != 1

    def get_user_vote_count(self, user: FakeUser) -> int:
        """Counts how many distinct options the given user has voted for in this poll."""
        return 0

    def can_user_cast_new_vote(self, user: FakeUser) -> bool:
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
    
    def has_user_voted(self, user: FakeUser) -> bool:
        """
        Checks if the given user has voted for at least one option in this poll.
        """
        return False

    def __str__(self):
        topic_title = "N/A"
        try:
            if self.topic_id and self.topic: # Check topic_id first to avoid query if it's None
                topic_title = self.topic.title
        except ArchiveTopic.DoesNotExist:
            # This case should ideally not be reached if on_delete=CASCADE works
            # and topic_id is always valid or poll is deleted.
            pass 
            
        return f"Poll: {self.question} (For Topic: {topic_title})"

    class Meta:
        ordering = ['-created_at']


class ArchivePollOptionVoters(models.Model):
    archivepolloption = models.ForeignKey('ArchivePollOption', on_delete=models.CASCADE)
    user = models.ForeignKey(FakeUser, on_delete=models.CASCADE, db_constraint=False)

    class Meta:
        unique_together = ('archivepolloption', 'user')


class ArchivePollOption(models.Model):
    poll = models.ForeignKey(
        'ArchivePoll',
        on_delete=models.CASCADE,
        related_name='archive_options', # Allows poll_instance.archive_options.all()
    )
    text = models.CharField(max_length=25500, unique=False)

    voters = models.ManyToManyField(
        FakeUser,
        through='ArchivePollOptionVoters',
        related_name='archive_poll_votes', # user_instance.archive_poll_votes.all() gets all options voted by a user
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
        except ArchivePoll.DoesNotExist:
             pass
        return f"Option: {self.text} (For Poll: {poll_question_snippet})"

    class Meta:
        # Ensures option text is unique within a specific poll.
        # unique_together = ('poll', 'text') # Removed to allow duplicate options in a poll
        ordering = ['id'] 

class ArchiveSubforum(models.Model):
    id = models.IntegerField(primary_key=True)
    parent = models.ManyToManyField('ArchiveTopic', related_name='archive_subforums', blank=True)
    title = models.CharField(max_length=25500, null=True, blank=True)
    description = models.CharField(max_length=25500, null=True, blank=True)
    is_hidden = models.BooleanField(default=False)

    @property
    def get_absolute_url(self):
        return f"/archive/f{self.topic.id}-{self.topic.slug}"

    def __str__(self):
        return f"Subforum: {self.topic.title} (ID: {self.topic.id})"
