from rest_framework import serializers
from ..models import Post, Profile
from django.contrib.auth.models import User

class PostDebugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'date_joined']

class ProfileDetailsSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(many=False, read_only=True)
    class Meta:
        model = Profile
        fields = ['user', 'messages_count', 'desc', 'localisation', 
                  'loisirs', 'birthdate',  'type', 'favorite_games', 
                  'zodiac_sign', 'gender', 'website', 'skype', 'signature', 'last_login']