from ..models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def posts_list(request): # This is a test endpoint to make sure the API is working
    posts = ArchivePost.objects.all()
    serializer = PostDebugSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def profile_details(request, userid):
    try:
        profile = ArchiveProfile.objects.get(id=userid)
    except ArchiveProfile.DoesNotExist:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    if profile.is_hidden and (not request.user.is_authenticated or request.user.id != profile.user.id):
        return Response({"detail": "Profile is hidden."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ProfileDetailsSerializer(profile)
    return Response(serializer.data)

@api_view(['GET'])
def post_simple(request, postid):
    try:
        post = ArchivePost.objects.get(id=postid)
    except ArchivePost.DoesNotExist:
        return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = PostBaseSerializer(post)
    return Response(serializer.data)

@api_view(['GET'])
def topic_details(request, topicid):
    try:
        topic = ArchiveTopic.objects.get(id=topicid)
    except ArchiveTopic.DoesNotExist:
        return Response({"detail": "Topic not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = TopicDetailsSerializer(topic)
    return Response(serializer.data)

@api_view(['GET'])
def post_details(request, postid):
    try:
        post = ArchivePost.objects.get(id=postid)
    except ArchivePost.DoesNotExist:
        return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = PostBaseSerializer(post) # TODO: [10] Use PostDetailsSerializer in the future
    return Response(serializer.data)

@api_view(['GET'])
def category(request, categoryid):
    try:
        category = ArchiveCategory.objects.get(id=categoryid)
    except ArchiveCategory.DoesNotExist:
        return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
    if category.is_hidden and (not request.user.is_authenticated or not request.user.is_staff):
        return Response({"detail": "Category is hidden."}, status=status.HTTP_403_FORBIDDEN)
    serializer = CategoryIndexSerializer(category)
    return Response(serializer.data)
