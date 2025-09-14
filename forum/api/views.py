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
    profile = Profile.objects.get(id=userid)
    serializer = ProfileDetailsSerializer(profile)
    return Response(serializer.data)

@api_view(['GET'])
def post_details(request, postid):
    post = Post.objects.get(id=postid)
    serializer = PostDebugSerializer(post)
    return Response(serializer.data)