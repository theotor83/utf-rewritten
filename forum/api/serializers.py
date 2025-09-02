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
        fields = ['username', 'date_joined']

class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = ForumGroup
        fields = ['name', 'description', 'color', 'priority', 'is_staff_group', 
                  'is_messages_group', 'minimum_messages']

class ProfileDetailsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    top_group = GroupSerializer(many=False, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'messages_count', 'desc', 'localisation', 
                  'loisirs', 'birthdate',  'type', 'favorite_games', 
                  'zodiac_sign', 'gender', 'website', 'skype', 'signature', 
                  'last_login', 'name_color', 'top_group', 'groups']
        
    def get_user(self, obj):
        """If email is public, include it in the user data."""
        user_data = UserShortSerializer(obj.user).data
        if obj.email_is_public:
            user_data['email'] = obj.user.email
        return user_data
