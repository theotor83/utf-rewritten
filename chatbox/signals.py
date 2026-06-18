from django.dispatch import Signal, receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from chatbox.chatboxstatemanager import user_change_signal

@receiver(user_change_signal)
def push_to_frontend(sender, **kwargs):
    print("Signal has been received, now pushing to frontend")
    channel_layer = get_channel_layer()
    message_data = kwargs.get('data', [])
    print("THIS WILL BE PUSHED TO FRONTEND: ", message_data)

    async_to_sync(channel_layer.group_send)(
        'frontend',
        {
            'type': 'user_change',
            'message': message_data
        }
    )