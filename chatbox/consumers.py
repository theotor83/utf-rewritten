import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

# TODO: MAKE IT SO THAT THE TOKEN IS THE ONLY THING THAT GOES FROM THE FRONTEND TO THE BACKEND

class ChatboxConsumer(WebsocketConsumer):
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
            received_username = text_data_json['username']
            received_name_color = text_data_json['name_color']
            received_user_token = text_data_json['user_token']
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'text': message_text,
                    'username': received_username,
                    'name_color': received_name_color,
                    'user_token': received_user_token,
                }
            )
            print(f'Message received : {message_text} by {received_username}, Name Color : {received_name_color}, Token : {received_user_token}')

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