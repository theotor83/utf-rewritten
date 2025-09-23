from rest_framework import serializers
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
    children = serializers.SerializerMethodField()


    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return ProfileMiniSerializer(obj.author.profile).data
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
            return obj.total_children
        return None
    
    def get_children(self, obj):
        """Return children info only if this is a subforum."""
        if obj.is_sub_forum:
            children = obj.children.all()
            return TopicCommonSerializer(children, many=True).data
        return None

    class Meta:
        model = Topic
        fields = TopicBaseSerializer.Meta.fields + [
            "description", "author", "last_post", "icon", "total_replies", "total_views",
            "total_children", "is_announcement", "is_sticky", "is_locked", "created_time", 
            "children"
        ]

class TopicDetailsSerializer(TopicCommonSerializer):
    """Full topic details."""
    parent = TopicBaseSerializer(read_only=True)
    class Meta(TopicCommonSerializer.Meta):
        fields = TopicCommonSerializer.Meta.fields + [
            "parent"
        ]


# --- Post Serializers ---

class PostBaseSerializer(serializers.ModelSerializer):
    """Common post fields."""
    text = serializers.CharField(read_only=True)
    author = serializers.SerializerMethodField()
    created_time = serializers.DateTimeField(read_only=True)
    url = serializers.ReadOnlyField(source='get_absolute_url')

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return ProfileMiniSerializer(obj.author.profile).data
        return None

    class Meta:
        model = Post
        fields = ["id", "text", "author", "created_time", "url"]

class PostTopicSerializer(PostBaseSerializer):
    """Full post details."""
    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return ProfileTopicSerializer(obj.author.profile).data
        return None
    class Meta(PostBaseSerializer.Meta):
        fields = PostBaseSerializer.Meta.fields + [
            "author"
        ]