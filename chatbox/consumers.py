from json import dumps
from channels.generic.websocket import WebsocketConsumer

class ChatboxConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.send(text_data=dumps({
            'type': 'connnected',
            'message': 'Connected!'
        }))

    def receive(self, text_data=None, bytes_data=None):
        pass

    def disconnect(self, close_code):
        pass