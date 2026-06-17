from chatbox.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from chatbox.chatboxstatemanager import ChatboxStateManager


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

@api_view(['GET'])
def users(request):
    """
    Will return the list of connected users.
    In reality, it will just use ChatboxStateManager to get all connected users.
    It will be formatted like this:
    {
        "count": 2,
        "users": [
            {
                "id": 1,
                "username": "Admin",
                "name_color": "#C02200"
            },
            {
                "id": 2,
                "username": "test",
                "name_color": "#FFFFFF"
            }
        ]
    }

    However, the implementation of the "users" list might change. Check the ChatboxStateManager class for more details.
    """
    user_list = ChatboxStateManager.get_connected_users()
    user_count = len(user_list)
    output_data = {
        "count": user_count,
        "users": user_list
    }
    return Response(output_data)

def test_chatbox(request):
    return render(request, 'test_chatbox.html')
