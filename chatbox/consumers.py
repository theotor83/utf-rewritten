import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from chatbox.tokenhandler import TokenHandler

class ChatboxConsumer(WebsocketConsumer):
    token_handler = TokenHandler()

    def connect(self):
        try:
            self.user = self.scope['user']
        except Exception as e:
            print(f"User could not connect to chatbox because the user could not be assigned : {e}")
            return

        try:
            self.username = self.user.username
        except Exception as e:
            print(f"User could not connect to chatbox because the username could not be assigned : {e}")
            return

        try:
            self.name_color = self.user.profile.name_color
        except Exception as e:
            print(f"User could not connect to chatbox because the name color could not be assigned : {e}. Selecting default color for user...")
            self.name_color = '#FFFFFF'
        self.room_group_name = 'Chatbox'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        if text_data_json.get('type') == 'chat_message':
            message_text = text_data_json['text']
            received_user_token = text_data_json['user_token']

            user_username = self.token_handler.get_username_from_token(received_user_token)
            user_name_color = self.token_handler.get_name_color_from_token(received_user_token)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'text': message_text,
                    'username': user_username,
                    'name_color': user_name_color,
                    'user_token': received_user_token,
                }
            )
            print(f'Message received : {message_text} by user with token {received_user_token}.\n Username might be {user_username}, and name color might be {user_name_color}.')

            print("Saving message...")
            from chatbox.models import ChatboxMessageManager # Else we get "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet."
            chatbox_message_manager = ChatboxMessageManager()
            chatbox_message = chatbox_message_manager.create_message(author=self.user, text=message_text)
            chatbox_message.save()
            print(f"Message saved with id {chatbox_message.id}.")


    def chat_message(self, event):
        message_text = event['text']
        username = event['username']
        name_color = event['name_color']
        user_token = event['user_token']

        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'text': message_text,
            'username': username,
            'name_color': name_color,
            'user_token': user_token
        }))

    def disconnect(self, close_code):
        pass