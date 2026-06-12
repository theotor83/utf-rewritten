from chatbox.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render


@api_view(['GET'])
def messages(request):
    # Handle fetching chat messages
    # Only limit to the most recent 100 messages for now, and then there can be a special archive endpoint (or param) in the future for the archive button
    previous_messages = ChatboxMessage.objects.order_by('-created_time')[:100]
    serializer = ChatboxMessageSerializer(previous_messages, many=True)
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
