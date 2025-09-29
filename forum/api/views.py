from ..models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination

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
    serializer = PostBaseSerializer(post) # TODO: [10] Use PostDetailsSerializer in the future
    return Response(serializer.data)

@api_view(['GET'])
def category(request, categoryid):
    try:
        category = Category.objects.get(id=categoryid)
    except Category.DoesNotExist:
        return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
    if category.is_hidden and (not request.user.is_authenticated or not request.user.is_staff):
        return Response({"detail": "Category is hidden."}, status=status.HTTP_403_FORBIDDEN)
    serializer = CategoryIndexSerializer(category)
    return Response(serializer.data)

@api_view(['GET'])
def category_details(request, categoryid):
    """Dedicated paginated endpoint for category details."""
    try:
        category = Category.objects.get(id=categoryid)
    except Category.DoesNotExist:
        return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
    if category.is_hidden and (not request.user.is_authenticated or not request.user.is_staff):
        return Response({"detail": "Category is hidden."}, status=status.HTTP_403_FORBIDDEN)
    
    page = request.query_params.get('page', 1)
    page_size = int(request.query_params.get('page_size', 50))
    max_page_size = 250

    if page_size > max_page_size:
        page_size = max_page_size

    all_topics = category.get_root_non_index_topics
    paginator = Paginator(all_topics, page_size)
    
    try:
        current_page = int(page)
        topics_page = paginator.page(current_page)
    except:
        current_page = 1
        topics_page = paginator.page(1)
    
    serializer = CategoryDetailsSerializer(
        category, 
        paginated_topics=topics_page.object_list
    )
    
    # Add pagination info to serializer
    pagination_info = {
        'current_page': current_page,
        'total_pages': paginator.num_pages,
        'total_items': paginator.count,
        'page_size': page_size,
        'has_next': topics_page.has_next(),
        'has_previous': topics_page.has_previous(),
        'next_page': topics_page.next_page_number() if topics_page.has_next() else None,
        'previous_page': topics_page.previous_page_number() if topics_page.has_previous() else None,
    }
    serializer._pagination_info = pagination_info
    
    return Response(serializer.data)