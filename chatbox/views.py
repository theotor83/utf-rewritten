from chatbox.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from chatbox.chatboxstatemanager import ChatboxStateManager
import datetime


@api_view(['GET'])
def messages(request):
    """
    Handle fetching chat messages
    Parameters:
        count=n where n is the number of messages
        before=epoch where epoch is the epoch time for the cutout
        before_id=n where n is the id of the cutout message (for which it is not included)

    Currently, before_id and before are not compatible.
    """
    count_param = request.GET.get("count", 100)
    before_date_param = request.GET.get("before", None)
    before_id_param = request.GET.get("before_id", None)

    count = int(count_param) if count_param else 100
    if count > 100:
        count = 100
    before_date = datetime.datetime.fromtimestamp(int(before_date_param)) if before_date_param else None
    before_id = int(before_id_param) if before_id_param else None

    if before_id:
        previous_messages = ChatboxMessage.objects.filter(id__lt=before_id).order_by('-created_time')[:count]
    elif before_date: # TODO [10]: Make it possible to chain both before_id and before_date
        previous_messages = ChatboxMessage.objects.filter(created_time__lte=before_date).order_by('-created_time')[:count]
    else:
        previous_messages = ChatboxMessage.objects.order_by('-created_time')[:count]
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
