from rest_framework import serializers
from ..models import *
from django.contrib.auth.models import User
# --- Debug Serializers ---

class PostDebugSerializer(serializers.ModelSerializer):
    """Serializer for debugging ArchivePost objects."""
    class Meta:
        model = ArchivePost
        fields = "__all__"


# --- User Serializers ---

class UserBaseSerializer(serializers.ModelSerializer):
    """Minimal user fields (used in subforum details when displaying the author)"""
    class Meta:
        model = FakeUser
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
        model = ArchiveForumGroup
        fields = ["id", "name", "color"]


class GroupDetailSerializer(GroupBaseSerializer):
    """Full group details."""
    class Meta(GroupBaseSerializer.Meta):
        fields = GroupBaseSerializer.Meta.fields + [
            "description", "priority", "is_staff_group",
            "minimum_messages"
        ]


# --- Profile Serializers ---

class ProfileBaseSerializer(serializers.ModelSerializer):
    """Common serializer logic for profiles."""
    user = serializers.SerializerMethodField()
    top_group = serializers.SerializerMethodField()

    def get_user(self, obj):
        if not obj.user:
            return None
        data = UserBaseSerializer(obj.user).data
        # Add email if public
        if getattr(obj, "email_is_public", False):
            data["email"] = obj.user.email
        return data

    def get_top_group(self, obj):
        group = obj.top_group or getattr(obj, "get_top_group", None)
        if callable(group):
            group = group()
        return GroupBaseSerializer(group).data if group else None

    class Meta:
        model = ArchiveProfile
        fields = ["id", "user", "name_color", "top_group"]


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
    profile_picture = serializers.CharField(read_only=True)
    """Used in topic views."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "profile_picture", "desc", "type", "zodiac_sign", "gender",
            "messages_count", "signature", "website", "skype"
        ]


class ProfileDetailsSerializer(ProfileBaseSerializer):
    """Used in profile details page."""
    groups = serializers.SerializerMethodField()
    profile_picture = serializers.CharField(read_only=True)

    def get_groups(self, obj):
        return GroupDetailSerializer(obj.groups.all(), many=True).data

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
        return getattr(obj, "archive_poll", None) is not None
    class Meta:
        model = ArchiveTopic
        fields = ["id", "title", "is_sub_forum", "slug", "has_poll", "url"]


class TopicCommonSerializer(TopicBaseSerializer):
    """Common topic (not subforum) fields."""
    author = serializers.SerializerMethodField()
    last_post = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    total_replies = serializers.IntegerField(source='display_replies', read_only=True)
    total_views = serializers.IntegerField(source='display_views', read_only=True)
    total_children = serializers.SerializerMethodField()
    is_announcement = serializers.BooleanField(read_only=True)
    is_pinned = serializers.BooleanField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'archiveprofile'):
            return ProfileMiniSerializer(obj.author.archiveprofile).data
        return None

    def get_last_post(self, obj):
        latest_post = obj.get_latest_message
        if latest_post and hasattr(latest_post, 'author'):
            return PostBaseSerializer(latest_post).data
        return None
    
    def get_icon(self, obj):
        if obj.icon:
            return f"/{obj.icon}"
        return None
    
    def get_total_children(self, obj):
        if obj.is_sub_forum:
            return obj.display_children
        return None
    
    class Meta:
        model = ArchiveTopic
        fields = TopicBaseSerializer.Meta.fields + [
            "description", "author", "last_post", "icon", "total_replies", "total_views",
            "total_children", "is_announcement", "is_pinned", "is_locked", "created_time"
        ]

class TopicDetailsSerializer(TopicCommonSerializer):
    """Full topic details."""
    children = serializers.SerializerMethodField()
    parent = TopicBaseSerializer(read_only=True)

    def get_children(self, obj):
        """Return children info only if this is a subforum."""
        if obj.is_sub_forum:
            children = obj.archive_children.all()
            return TopicCommonSerializer(children, many=True).data
        return None
    class Meta(TopicCommonSerializer.Meta):
        fields = TopicCommonSerializer.Meta.fields + [
            "children", "parent"
        ]


# --- Post Serializers ---

class PostBaseSerializer(serializers.ModelSerializer):
    """Common post fields."""
    author = serializers.SerializerMethodField()
    created_time = serializers.DateTimeField(read_only=True)
    url = serializers.ReadOnlyField(source='get_absolute_url')

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'archiveprofile'):
            return ProfileMiniSerializer(obj.author.archiveprofile).data
        return None

    class Meta:
        model = ArchivePost
        fields = ["id", "author", "created_time", "url"]




# --- Category Serializers ---

class CategoryBaseSerializer(serializers.ModelSerializer):
    """Minimal category fields."""
    url = serializers.ReadOnlyField(source='get_absolute_url')
    class Meta:
        model = ArchiveCategory
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
