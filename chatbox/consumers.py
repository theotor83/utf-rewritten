import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class ChatboxConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'Chatbox'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        if text_data_json.get('type') == 'chat_message':
            message_text = text_data_json['text']
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'text': message_text
                }
            )
            print(f'Message received : {message_text}')

    def chat_message(self, event):
        message_text = event['text']

        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message_text
        }))

    def disconnect(self, close_code):
        pass