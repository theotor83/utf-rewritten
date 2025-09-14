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
        model = Profile
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
    profile_picture = serializers.ImageField(read_only=True)
    """Used in topic views."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "profile_picture", "desc", "type", "zodiac_sign", "gender",
            "messages_count", "signature", "website", "skype"
        ]


class ProfileDetailsSerializer(ProfileBaseSerializer):
    """Used in profile details page."""
    groups = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(read_only=True)

    def get_groups(self, obj):
        return GroupDetailSerializer(obj.groups.all(), many=True).data

    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + [
            "messages_count", "desc", "localisation", "loisirs", "birthdate",
            "type", "favorite_games", "zodiac_sign", "gender", "website",
            "skype", "signature", "last_login", "groups", "profile_picture"
        ]
