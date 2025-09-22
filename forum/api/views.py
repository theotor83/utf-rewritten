from ..models import Post, Profile
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def posts_list(request): # This is a test endpoint to make sure the API is working
    posts = Post.objects.all()
    serializer = PostDebugSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def profile_details(request, userid):
    try:
        profile = Profile.objects.get(id=userid)
    except Profile.DoesNotExist:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    if profile.is_hidden and (not request.user.is_authenticated or request.user.id != profile.user.id):
        return Response({"detail": "Profile is hidden."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ProfileDetailsSerializer(profile)
    return Response(serializer.data)

@api_view(['GET'])
def post_simple(request, postid):
    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = PostBaseSerializer(post)
    return Response(serializer.data)

@api_view(['GET'])
def topic_details(request, topicid):
    try:
        topic = Topic.objects.get(id=topicid)
    except Topic.DoesNotExist:
        return Response({"detail": "Topic not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = TopicDetailsSerializer(topic)
    return Response(serializer.data)

@api_view(['GET'])
def post_details(request, postid):
    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = PostTopicSerializer(post)
    return Response(serializer.data)