from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils.text import slugify
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from collections import deque
# Choices for CharField(choices = ...)
import os
import uuid
from django.utils import timezone

# def profile_picture_upload_path(instance, filename):
#     """Generate a file path with username, original filename, and a 4-character UUID"""
#     username = instance.user.username  # Assuming a OneToOne relation with User
#     ext = filename.split('.')[-1]  # Get the file extension
#     base_filename = os.path.splitext(filename)[0]  # Get filename without extension
#     short_uuid = uuid.uuid4().hex[:4]  # Generate a 4-character UUID
#     new_filename = f"{username}_{base_filename}_{short_uuid}.{ext}"  # Construct new filename
#     return os.path.join("images/profile_picture", new_filename)

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

    @property
    def get_top_group(self):
        return self.groups.order_by('-priority').first()
    
    @property
    def get_group_color(self):
        top_group = self.get_top_group
        return top_group.color
    
    @property
    def is_user_staff(self):
        return self.groups.filter(is_staff_group=True).exists()
    
    @property
    def get_user_age(self):
        """Get the user's age in years."""
        if self.birthdate:
            today = timezone.now()
            age = today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
            return age
        return 0
    
    def save(self, *args, **kwargs):

        
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

        
    
    def __str__(self):
        return f"{self.user}'s profile"


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

            # Update latest message time for the topic
            if self.topic:
                latest_message = self.topic.get_latest_message
                if latest_message:
                    self.topic.last_message_time = timezone.now() # this is ugly and should be fixed with a signal or something
                    self.topic.save()
                    print(f"Latest message time for {self.topic} updated to {self.topic.last_message_time}")
                else:
                    print("No messages found")

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
                            self.author.profile.save()
                            print(f"{self.author} promoted to {group}")

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
    
    @property
    def is_root_topic(self):
        return self.parent == None
    
    @property
    def get_latest_message(self):

        if self.is_sub_forum:
            # Collect all descendant topics including self using BFS
            all_topics = []
            queue = deque([self])

            while queue:
                current_topic = queue.popleft()
                all_topics.append(current_topic)
                queue.extend(current_topic.children.all())

            # Get the latest post from all collected topics
            latest_post = Post.objects.filter(topic__in=all_topics).order_by('-created_time').first()
            return latest_post
        
        else:
            latest_post = Post.objects.filter(topic=self).order_by('-created_time').first()
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
        return self.children.filter(is_sub_forum=True)
    
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

        if self.pk is None:
            if self.parent:   # Increment parent's children count when new topic is created (total_replies will be handled by the Post's save method)
                self.parent.total_children += 1
                self.parent.save()

            if self.is_sub_forum: # Make total replies 0 instead of -1
                self.total_replies = 0

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