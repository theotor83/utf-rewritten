from rest_framework import serializers
from chatbox.models import *
from forum.api.serializers import ProfileBaseSerializer

class ProfileChatboxSerializer(ProfileBaseSerializer):
    """Barebone serializer for chatbox messages."""
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields

    def get_name_color(self, obj):
        if obj.top_group and obj.top_group.color:
            return obj.top_group.color
        return obj.name_color

    def get_user(self, obj):
        # Here, user means username
        if obj.user:
            return obj.user.username

class ChatboxMessageSerializer(serializers.Serializer):
    """Serializer for chatbox messages."""
    id = serializers.IntegerField(read_only=True)
    author = ProfileChatboxSerializer(read_only=True, source='author.profile')
    text = serializers.CharField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    quoted_message = serializers.SerializerMethodField()

    def get_quoted_message(self, obj):
        if obj.quoted_message:
            quote_profile = getattr(obj.quoted_message.author, 'profile', None)
            quote_color = "#FFFFFF"
            if quote_profile:
                if quote_profile.top_group and quote_profile.top_group.color:
                    quote_color = quote_profile.top_group.color
                else:
                    quote_color = quote_profile.name_color

            return {
                "id": obj.quoted_message.id,
                "text": obj.quoted_message.text,
                "author": {
                    "username": obj.quoted_message.author.username,
                    "name_color": quote_color,
                },
                "created_time": obj.quoted_message.created_time.isoformat()
            }
        return None