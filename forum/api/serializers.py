from rest_framework import serializers
from ..models import *
from django.contrib.auth.models import User

class PostDebugSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = '__all__'

class UserShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'date_joined']

class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = ForumGroup
        fields = ['id', 'name', 'description', 'color', 'priority', 'is_staff_group', 
                  'is_messages_group', 'minimum_messages']

class ProfileDetailsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    top_group = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'messages_count', 'desc', 'localisation', 
                  'loisirs', 'birthdate',  'type', 'favorite_games', 
                  'zodiac_sign', 'gender', 'website', 'skype', 'signature', 
                  'last_login', 'name_color', 'top_group', 'groups']
        
    def get_user(self, obj):
        """If email is public, include it in the user data."""
        if not obj.user:
            return None
            
        user_data = UserShortSerializer(obj.user).data
        if obj.email_is_public:
            user_data['email'] = obj.user.email
        return user_data
    
    def get_top_group(self, obj):
        """Serialize the top group using GroupSerializer with fallback logic."""
        group = obj.top_group or getattr(obj, 'get_top_group', None)
        if callable(group):  # In case get_top_group is a method rather than @property
            group = group()
        if group:
            return GroupSerializer(group).data
        return None
    
    def get_groups(self, obj):
        """Serialize all groups using GroupSerializer."""
        return GroupSerializer(obj.groups.all(), many=True).data

class ProfileMiniSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    top_group = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'name_color', 'top_group']
        
    def get_user(self, obj):
        """Return basic user information."""
        if not obj.user:
            return None
        return UserShortSerializer(obj.user).data
    
    def get_top_group(self, obj):
        """Serialize the top group using fallback property on the model."""
        group = obj.top_group or getattr(obj, 'get_top_group', None)
        if callable(group):
            group = group()
        if group:
            return GroupSerializer(group).data
        return None