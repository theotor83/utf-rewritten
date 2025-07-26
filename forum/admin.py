# forum/admin.py

from django.contrib import admin
from . import models
from django.utils.html import format_html
from django.urls import reverse
from django.template.defaultfilters import truncatechars

# Inlines

class PostInline(admin.TabularInline):
    model = models.Post
    fields = ('author', 'text', 'created_time')
    readonly_fields = ('author', 'created_time')
    extra = 0
    ordering = ('created_time',)
    show_change_link = True

class TopicInline(admin.TabularInline):
    model = models.Topic
    fields = ('title', 'author', 'created_time', 'is_sub_forum', 'is_locked')
    readonly_fields = ('author', 'created_time')
    extra = 0
    show_change_link = True

class PollOptionInline(admin.TabularInline):
    model = models.PollOption
    fields = ('text', 'vote_count_display')
    readonly_fields = ('vote_count_display',)
    extra = 1

    def vote_count_display(self, obj):
        return obj.get_vote_count
    vote_count_display.short_description = "Votes"

class PrivateMessageInline(admin.TabularInline):
    model = models.PrivateMessage
    fields = ('author', 'recipient', 'text', 'created_at', 'is_read')
    readonly_fields = ('created_at',)
    extra = 0
    ordering = ('created_at',)
    show_change_link = True

class ProfileInline(admin.TabularInline): # For ForumGroup
    model = models.Profile.groups.through
    verbose_name = "Member"
    verbose_name_plural = "Members"
    extra = 0

    #def profile_user(self, instance):
    #    return instance.profile.user.username
    #profile_user.short_description = 'User'


# ModelAdmins

@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_top_group_display', 'messages_count', 'birthdate', 'last_login')
    search_fields = ('user__username', 'user__email')
    list_filter = ('groups', 'gender', 'type')
    #inlines = [PostInline]
    readonly_fields = ('last_login', 'display_user_posts')
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'groups', 'messages_count', 'last_login')
        }),
        ('Personal Info', {
            'fields': ('birthdate', 'gender', 'type', 'zodiac_sign', 'desc', 'localisation', 'loisirs')
        }),
        ('Contact & Preferences', {
            'fields': ('website', 'skype', 'email_is_public')
        }),
        ('Forum Specific', {
            'fields': ('favorite_games', 'signature', 'display_user_posts')
        }),
        ('Other', {
            'fields': ('upload_size',)
        }),
    )
    filter_horizontal = ('groups',)

    def get_top_group_display(self, obj):
        top_group = obj.get_top_group
        if top_group:
            return format_html('<span style="color: {};">{}</span>', top_group.color, top_group.name)
        return "N/A"
    get_top_group_display.short_description = "Top Group"
    get_top_group_display.admin_order_field = 'groups__priority' # Allows sorting

    def display_user_posts(self, obj):
        if obj.user:
            posts = models.Post.objects.filter(author=obj.user).order_by('-created_time')[:10] # Display recent 10 posts
            if not posts:
                return "No posts by this user."
            
            html = "<strong>Recent Posts (up to 10):</strong><ul>"
            for post in posts:
                post_admin_url = reverse('admin:forum_post_change', args=[post.pk])
                topic_title = post.topic.title if post.topic else "N/A"
                html += f'<li><a href="{post_admin_url}">{topic_title} ({post.created_time.strftime("%Y-%m-%d %H:%M")})</a>: {truncatechars(post.text, 75)}</li>'
            html += "</ul>"
            
            all_posts_url = reverse('admin:forum_post_changelist') + f'?author__id__exact={obj.user.pk}'
            html += f'<p><a href="{all_posts_url}">View all posts by this user ({obj.messages_count})</a></p>'
            return format_html(html)
        return "N/A"
    display_user_posts.short_description = "User Posts"

    def save_related(self, request, form, formsets, change): # This method is called after saving the main form, now used to update name_color dynamically
        # Save M2M fields now
        super().save_related(request, form, formsets, change)
        # Now, update name_color based on the top group
        user = form.instance
        top_group = user.get_top_group
        user.name_color = top_group.color if top_group and top_group.color else "#FFFFFF"
        user.save(update_fields=['name_color'])

@admin.register(models.ForumGroup)
class ForumGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'is_staff_group', 'is_messages_group', 'minimum_messages', 'member_count')
    search_fields = ('name',)
    list_filter = ('is_staff_group', 'is_messages_group')
    # inlines = [ProfileInline] # This can be very heavy if there are many users.
                               # I already have filter_horizontal on ProfileAdmin for 'groups'
    ordering = ('-priority',)

    def member_count(self, obj):
        return obj.users.count()
    member_count.short_description = "Members"

@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'author_link', 'topic_link', 'created_time', 'update_count')
    search_fields = ('text', 'author__username', 'topic__title')
    list_filter = ('created_time',)
    readonly_fields = ('created_time', 'updated_time')
    date_hierarchy = 'created_time'
    ordering = ('-created_time',)

    def author_link(self, obj):
        if obj.author:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.author.pk}/change/', 
                               obj.author.username)
        return "N/A"
    author_link.short_description = "Author"

    def topic_link(self, obj):
        if obj.topic:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/topic/{obj.topic.pk}/change/', 
                               obj.topic.title)
        return "N/A"
    topic_link.short_description = "Topic"


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_link', 'category_link', 'parent_link', 'created_time', 'last_message_time', 'total_replies', 'total_views', 'is_sub_forum', 'is_locked', 'has_poll_display')
    search_fields = ('title', 'description', 'author__username')
    list_filter = ('is_sub_forum', 'is_locked', 'is_pinned', 'is_announcement', 'category', 'created_time', 'latest_message')
    readonly_fields = ('created_time', 'last_message_time', 'slug')
    inlines = [PostInline] # Shows posts directly in the topic admin page
    ordering = ('-last_message_time',)
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'slug', 'description', 'icon')
        }),
        ('Hierarchy & Type', {
            'fields': ('category', 'parent', 'is_sub_forum', 'latest_message')
        }),
        ('Status & Stats', {
            'fields': ('is_locked', 'is_pinned', 'is_announcement', 'is_index_topic', 'has_subforum_children', 'total_views', 'total_replies')
        }),
        ('Timestamps', {
            'fields': ('created_time', 'last_message_time')
        }),
    )

    def author_link(self, obj):
        if obj.author:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.author.pk}/change/', 
                               obj.author.username)
        return "N/A"
    author_link.short_description = "Author"

    def category_link(self, obj):
        if obj.category:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/category/{obj.category.pk}/change/', 
                               obj.category.name)
        return "N/A"
    category_link.short_description = "Category"

    def parent_link(self, obj):
        if obj.parent:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/topic/{obj.parent.pk}/change/', 
                               obj.parent.title)
        return "N/A"
    parent_link.short_description = "Parent Forum"

    def has_poll_display(self, obj):
        try:
            return bool(obj.poll)
        except models.Poll.DoesNotExist:
            return False
    has_poll_display.short_description = "Has Poll?"
    has_poll_display.boolean = True

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('poll')


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_hidden', 'topic_count')
    search_fields = ('name',)
    readonly_fields = ('slug',)
    # inlines = [TopicInline] # Can be very long if many topics.
    
    def topic_count(self, obj):
        return obj.topic_set.count() # Counts all topics directly under this category
    topic_count.short_description = "Topics"

@admin.register(models.Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_users', 'total_messages', 'online_record', 'online_record_date')
    filter_horizontal = ('announcement_topics',)

@admin.register(models.TopicReadStatus)
class TopicReadStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic_link', 'last_read')
    search_fields = ('user__username', 'topic__title')
    readonly_fields = ('last_read',)

    def topic_link(self, obj):
        if obj.topic:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/topic/{obj.topic.pk}/change/', 
                               obj.topic.title)
        return "N/A"
    topic_link.short_description = "Topic"

@admin.register(models.SmileyCategory)
class SmileyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'smiley_count')
    search_fields = ('name',)
    filter_horizontal = ('smileys',)

    def smiley_count(self, obj):
        return obj.smileys.count()
    smiley_count.short_description = "Smileys"

@admin.register(models.Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'topic_link', 'created_at', 'days_to_vote', 'max_choices_per_user', 'can_change_vote', 'is_active_display')
    search_fields = ('question', 'topic__title')
    list_filter = ('created_at', 'days_to_vote', 'can_change_vote')
    inlines = [PollOptionInline]
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('topic', 'question')
        }),
        ('Voting Rules', {
            'fields': ('days_to_vote', 'max_choices_per_user', 'can_change_vote')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def topic_link(self, obj):
        if obj.topic:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/topic/{obj.topic.pk}/change/', 
                               obj.topic.title)
        return "N/A"
    topic_link.short_description = "Topic"

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.short_description = "Active?"
    is_active_display.boolean = True

@admin.register(models.PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'poll_link', 'vote_count_display')
    search_fields = ('text', 'poll__question')
    readonly_fields = ('vote_count_display',)
    filter_horizontal = ('voters',)

    def poll_link(self, obj):
        if obj.poll:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/poll/{obj.poll.pk}/change/', 
                               obj.poll.question[:50] + "...")
        return "N/A"
    poll_link.short_description = "Poll"

    def vote_count_display(self, obj):
        return obj.get_vote_count
    vote_count_display.short_description = "Votes"

@admin.register(models.PrivateMessageThread)
class PrivateMessageThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_link', 'recipient_link', 'created_at', 'updated_at', 'message_count')
    search_fields = ('title', 'author__username', 'recipient__username')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)
    inlines = [PrivateMessageInline]

    def author_link(self, obj):
        if obj.author:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.author.pk}/change/', 
                               obj.author.username)
        return "N/A"
    author_link.short_description = "Author"

    def recipient_link(self, obj):
        if obj.recipient:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.recipient.pk}/change/', 
                               obj.recipient.username)
        return "N/A"
    recipient_link.short_description = "Recipient"

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"

@admin.register(models.PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('thread_link', 'author_link', 'recipient_link', 'created_at', 'is_read', 'text_preview')
    search_fields = ('text', 'author__username', 'recipient__username', 'thread__title')
    list_filter = ('created_at', 'updated_at', 'is_read')
    readonly_fields = ('created_at', 'updated_at', 'get_relative_id')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def thread_link(self, obj):
        if obj.thread:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/forum/privatemessagethread/{obj.thread.pk}/change/', 
                               obj.thread.title or f"Thread #{obj.thread.pk}")
        return "N/A"
    thread_link.short_description = "Thread"

    def author_link(self, obj):
        if obj.author:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.author.pk}/change/', 
                               obj.author.username)
        return "N/A"
    author_link.short_description = "Author"

    def recipient_link(self, obj):
        if obj.recipient:
            return format_html('<a href="{}">{}</a>', 
                               f'/admin/auth/user/{obj.recipient.pk}/change/', 
                               obj.recipient.username)
        return "N/A"
    recipient_link.short_description = "Recipient"

    def text_preview(self, obj):
        return truncatechars(obj.text, 50)
    text_preview.short_description = "Message Preview"
