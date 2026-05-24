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
    author = ProfileChatboxSerializer(read_only=True, source='author.profile')
    text = serializers.CharField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
