from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from ..models import *
from django.contrib.auth.models import User
# --- Debug Serializers ---

class PostDebugSerializer(serializers.ModelSerializer):
    """Serializer for debugging Post objects."""
    class Meta:
        model = Post
        fields = "__all__"


# --- User Serializers ---

class UserBaseSerializer(serializers.ModelSerializer):
    """Minimal user fields (used in subforum details when displaying the author)"""
    class Meta:
        model = User
        fields = ["id", "username"]


class UserExtendedSerializer(UserBaseSerializer):
    """Extended user serializer (most common)."""
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ["date_joined"]


# --- Group Serializers ---

class GroupBaseSerializer(serializers.ModelSerializer):
    """Minimal group fields (common)."""
    class Meta:
        model = ForumGroup
        fields = ["id", "name", "color"]


class GroupDetailSerializer(GroupBaseSerializer):
    """Full group details."""
    class Meta(GroupBaseSerializer.Meta):
        fields = GroupBaseSerializer.Meta.fields + [
            "description", "priority", "is_staff_group",
            "is_messages_group", "minimum_messages"
        ]


# --- Profile Serializers ---

class ProfileBaseSerializer(serializers.ModelSerializer):
    """Common serializer logic for profiles."""
    user = UserBaseSerializer(read_only=True, allow_null=True)
    top_group = GroupBaseSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "name_color", "top_group"]
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Add email if public
        user_data = data.get('user')
        if user_data and getattr(instance, "email_is_public", False) and instance.user:
            data['user']['email'] = instance.user.email
            
        # Handle top_group property method
        if not data.get('top_group') and hasattr(instance, 'get_top_group'):
            top_group = instance.get_top_group
            data['top_group'] = GroupBaseSerializer(top_group).data if top_group else None
            
        return data


class ProfileMiniSerializer(ProfileBaseSerializer):
    """Minimal profile (used in subforum details when displaying the author)."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields


class ProfileListSerializer(ProfileBaseSerializer):
    """Used in memberlist page."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "messages_count", "last_login", "website"
        ]

class ProfileTopicSerializer(ProfileBaseSerializer):
    profile_picture = serializers.ImageField(read_only=True)
    """Used in topic views."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "profile_picture", "desc", "type", "zodiac_sign", "gender",
            "messages_count", "signature", "website", "skype"
        ]


class ProfileDetailsSerializer(ProfileBaseSerializer):
    """Used in profile details page."""
    groups = GroupDetailSerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(read_only=True)

    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "messages_count", "desc", "localisation", "loisirs", "birthdate",
            "type", "favorite_games", "zodiac_sign", "gender", "website",
            "skype", "signature", "last_login", "groups", "profile_picture"
        ]


# --- Topic Serializers ---

class TopicBaseSerializer(serializers.ModelSerializer):
    """Minimal topic fields."""
    is_sub_forum = serializers.BooleanField(read_only=True)
    url = serializers.ReadOnlyField(source='get_absolute_url')
    has_poll = serializers.SerializerMethodField()

    def get_has_poll(self, obj):
        return getattr(obj, "poll", None) is not None
    
    class Meta:
        model = Topic
        fields = ["id", "title", "is_sub_forum", "slug", "has_poll", "url"]


class TopicCommonSerializer(TopicBaseSerializer):
    """Common topic (not subforum) fields."""
    author = serializers.SerializerMethodField()
    last_post = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    total_replies = serializers.IntegerField(read_only=True)
    total_views = serializers.IntegerField(read_only=True)
    total_children = serializers.SerializerMethodField(read_only=True)
    is_announcement = serializers.BooleanField(read_only=True)
    is_sticky = serializers.BooleanField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return ProfileMiniSerializer(obj.author.profile).data
        return None

    def get_last_post(self, obj):
        latest_post = obj.get_latest_message
        if latest_post and hasattr(latest_post, 'author'):
            return PostMiniSerializer(latest_post).data
        return None
    
    def get_icon(self, obj):
        if obj.icon:
            return f"/{obj.icon}"
        return None
    
    def get_total_children(self, obj):
        if obj.is_sub_forum:
            return obj.total_children
        return None

    class Meta:
        model = Topic
        fields = TopicBaseSerializer.Meta.fields + [
            "description", "author", "last_post", "icon", "total_replies", "total_views",
            "total_children", "is_announcement", "is_sticky", "is_locked", "created_time"
        ]

class TopicDetailsSerializer(TopicCommonSerializer):
    """Full topic details."""
    children = serializers.SerializerMethodField()
    parent = TopicBaseSerializer(read_only=True)

    def get_children(self, obj):
        """Return children info only if this is a subforum."""
        if obj.is_sub_forum:
            children = obj.children.all()
            return TopicCommonSerializer(children, many=True).data
        return None
    class Meta(TopicCommonSerializer.Meta):
        fields = TopicCommonSerializer.Meta.fields + [
            "children", "parent"
        ]


# --- Post Serializers ---

class PostMiniSerializer(serializers.ModelSerializer):
    """Used in topic last_post field."""
    author = serializers.SerializerMethodField()
    created_time = serializers.DateTimeField(read_only=True)
    url = serializers.ReadOnlyField(source='get_absolute_url')

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return ProfileMiniSerializer(obj.author.profile).data
        return None

    class Meta:
        model = Post
        fields = ["id", "author", "created_time", "url"]

class PostBaseSerializer(PostMiniSerializer):
    """Common post fields."""
    text = serializers.CharField(read_only=True)
    class Meta(PostMiniSerializer.Meta):
        fields = PostMiniSerializer.Meta.fields + [
            "text"
        ]



# --- Category Serializers ---

class CategoryBaseSerializer(serializers.ModelSerializer):
    """Minimal category fields."""
    url = serializers.ReadOnlyField(source='get_absolute_url')
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "url"]

class CategoryIndexSerializer(CategoryBaseSerializer):
    """Category with index topics (for index page)."""
    index_topics = serializers.SerializerMethodField()

    def get_index_topics(self, obj):
        index_topics = obj.get_all_index_topics
        return TopicCommonSerializer(index_topics, many=True).data

    class Meta(CategoryBaseSerializer.Meta):
        fields = CategoryBaseSerializer.Meta.fields + [
            "index_topics"
        ]

class CategoryDetailsSerializer(CategoryBaseSerializer):
    """Category with paginated topics (for category details page with pagination supported)."""
    subforums = serializers.SerializerMethodField()
    announcements = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    pagination = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.paginated_topics = kwargs.pop('paginated_topics', None)
        super().__init__(*args, **kwargs)

    def get_subforums(self, obj):
        subforums = obj.get_all_subforums
        if not subforums:
            return None
        return TopicCommonSerializer(subforums, many=True).data
    
    def get_announcements(self, obj):
        forum = Forum.objects.first()
        return TopicCommonSerializer(forum.get_announcement_topics, many=True).data

    def get_topics(self, obj):
        if self.paginated_topics:
            return TopicCommonSerializer(self.paginated_topics, many=True).data
        return None
    
    def get_pagination(self, obj):
        # This will be set by the view when pagination info is available
        return getattr(self, '_pagination_info', None)

    class Meta(CategoryBaseSerializer.Meta):
        fields = CategoryBaseSerializer.Meta.fields + [
            "subforums", "announcements", "topics", "pagination"
        ]
