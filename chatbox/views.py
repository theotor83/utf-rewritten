from chatbox.models import *
from chatbox.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.shortcuts import render

# Create your views here.

@api_view(['POST'])
def connect(request):
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    # Get or create the token for the authenticated user to connect to the chatbox websocket
    token = Token.objects.get_or_create(user=request.user)
    
    return Response({"token": token.key}, status=status.HTTP_200_OK)

@api_view(['POST'])
def message(request):
    # Handle incoming chat message
    if not request.user.is_authenticated: # Maybe replace this with token authentication in the future ?
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    text = request.data.get('text')
    if not text:
        return Response({"detail": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)

    # TODO [10]: Add rate limiting to prevent spam, and other checks and stuff...
    ChatboxMessage.objects.create(
        author=request.user,
        text=text
    ) # The id and timestamp will be automatically generated
    return Response({"detail": "Message sent."}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def messages(request):
    # Handle fetching chat messages
    # Only limit to the most recent 100 messages for now, and then there can be a special archive endpoint (or param) in the future for the archive button
    messages = ChatboxMessage.objects.order_by('-created_time')[:100]
    serializer = ChatboxMessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def message_details(request, messageid):
    # I honestly don't know if this endpoint will be useful, but it doesn't hurt to have it
    try:
        message = ChatboxMessage.objects.get(id=messageid)
    except ChatboxMessage.DoesNotExist:
        return Response({"detail": "Message not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ChatboxMessageSerializer(message)
    return Response(serializer.data)

def test_chatbox(request):
    return render(request, 'test_chatbox.html')
