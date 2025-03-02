from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils.text import slugify
from django.core.exceptions import ValidationError

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
    ("Cancer", "Cancer (21juin-23juil)"),
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

# Create your models here.

class ForumGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    priority = models.IntegerField(unique=True)
    description = models.TextField()
    is_staff_group = models.BooleanField(default=False)
    minimum_messages = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=10, default="#FFFFFF")
    icon = models.ImageField(null=True, blank=True, upload_to='images/group_icons/')

    class Meta:
        ordering = ['-priority']

    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(null=True, blank=True, upload_to='images/profile_picture/')
    groups = models.ManyToManyField(ForumGroup, related_name='users')
    messages_count = models.IntegerField(default=0)
    desc = models.CharField(null=True, blank=True, max_length=255)
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

    @property
    def get_top_group(self):
        return self.groups.order_by('-priority').first()
    
    @property
    def get_group_color(self):
        top_group = self.get_top_group
        return top_group.color
    
    def __str__(self):
        return f"{self.user}'s profile"


class Category(models.Model):
    name = models.CharField(max_length=60, default="DEFAULT_CATEGORY_NAME")
    slug = models.SlugField(max_length=255, blank=True)
    index_topics = models.ManyToManyField('Topic', related_name='index_topics', blank=True) 

    @property 
    def get_index_sub_forums(self):
        """THIS METHOD IS DEPRECATED AND SHOULD NOT BE USED"""
        return Topic.objects.filter(category=self, is_index_topic=True)
    
    def save(self, *args, **kwargs):
        
        self.slug = f"{slugify(self.name)}"

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

    def save(self, *args, **kwargs):
        
        if self.topic:
            self.topic.last_message_time = self.created_time
            self.topic.total_posts += 1

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
    last_message_time = models.DateTimeField(auto_now_add=True)
    total_posts = models.IntegerField(default=0)
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
        from collections import deque

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
    
    def clean(self):

        if self.parent != None:
            if self.parent.is_sub_forum == False:
                raise ValidationError("The parent of this topic is not a sub forum.")
        

    def save(self, *args, **kwargs):

        self.slug = f"{slugify(self.title)}"

        # Sync category with parent's category if parent exists
        if self.parent and not self.category:
            self.category = self.parent.category 

        if self.parent:
            self.parent.total_posts += 1
        
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

    @property
    def get_announcement_topics(self):
        if self.annoucement_topics.count() == 0:
            self.annoucement_topics = Topic.objects.filter(is_annoucement=True)
        else:
            return self.annoucement_topics
        
    def __str__(self):
        return self.name