import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from chatbox.tokenhandler import TokenHandler
from chatbox.chatboxmessagehandler import ChatboxMessageHandler
from chatbox.chatboxstatemanager import ChatboxStateManager

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
        self.room_group_name = 'Chatbox' # I'm scared of making this the chatbox_instance's title...
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        ChatboxStateManager.add_connected_user({"id": self.user.id, "username": self.username, "name_color": self.name_color})

        async_to_sync(self.channel_layer.group_add)(
            'frontend',  # The exact group name your signal uses
            self.channel_name  # The unique ID for this specific user's socket
        ) # This is to connect with the user changes signals

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        print(f"Raw text data received: {text_data_json}")
        if text_data_json.get('type') == 'chat_message':
            message_text = text_data_json['text']
            received_user_token = text_data_json['user_token']

            user_username = self.token_handler.get_username_from_token(received_user_token)
            user_name_color = self.token_handler.get_name_color_from_token(received_user_token)
            user_id = self.token_handler.get_user_id_from_token(received_user_token)

            quoted_message_instance = None

            if ChatboxMessageHandler.message_has_valid_quote(message_text):
                # These checks below are redundant, but I will keep them...
                # TODO [5]: Refactor this piece of code so that ChatboxMessageHandler can handle it itself? It still works...
                quoted_message_id = ChatboxMessageHandler.return_quoted_message_id(message_text)

                if quoted_message_id:
                    from chatbox.models import ChatboxMessage # Still the django app is not ready error
                    try:
                        quoted_message_instance = ChatboxMessage.objects.get(id=quoted_message_id)
                    except ChatboxMessage.DoesNotExist:
                        print(f"Message with id {quoted_message_id} does not exist.")
                    if not quoted_message_instance:
                        print(f"Quoted message with id {quoted_message_id} not found, ignoring quote.")

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'text': message_text,
                    'author': {
                        'id': int(user_id),
                        'user': {
                            'id': int(user_id), # Again, this is to match the API exactly even though it's redundant
                            'username': user_username,
                        },
                        'name_color': user_name_color,
                        'top_group': {
                            'color': user_name_color, # HACK
                        }
                    }
                }
            )
            print(f'Message received : "{message_text}".\n Username might be {user_username}, and name color might be {user_name_color}.')

            print("Saving message...")
            from chatbox.models import ChatboxMessageManager # Else we get "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet."
            if quoted_message_instance is not None:
                print("The message is a quote, saving with quoted message reference while making sure to remove the tag...")
                message_text = ChatboxMessageHandler.return_text_no_quote(message_text)
            chatbox_message = ChatboxMessageManager.create_message(author=self.user, text=message_text, quoted_message=quoted_message_instance)
            chatbox_message.save()
            print(f"Message saved with id {chatbox_message.id}.")


    def chat_message(self, event):
        message_text = event['text']
        username = event['author']['user']['username']
        name_color = event['author']['name_color']
        author_id = event['author']['id']
        is_quote = False
        quote_msg_id = None

        if ChatboxMessageHandler.message_has_valid_quote(message_text):
            is_quote = True
            quote_msg_id = ChatboxMessageHandler.return_quoted_message_id(message_text)

        output_dict = {
            'type': 'chat_message',
            'text': ChatboxMessageHandler.return_text_no_quote(message_text),
            'author': {
                'id': int(author_id),
                'user': {
                    'id': int(author_id), # This is to match the API, I know this is redundant
                    'username': username,
                },
                'name_color': name_color,
                'top_group': {
                    'color': name_color, # HACK
                }
            }
        }

        if is_quote and quote_msg_id is not None:
            from chatbox.models import ChatboxMessage # Still the django app is not ready error
            quoted_msg_instance = ChatboxMessage.objects.get(id=quote_msg_id)
            if not quoted_msg_instance:
                print(f"Message with id {quote_msg_id} not found, ignoring quote.")
            else:
                quote_dict = {
                    'id': int(quote_msg_id),
                    'text': quoted_msg_instance.text,
                    'created_time': quoted_msg_instance.created_time.isoformat(),
                    'author': {}
                }
                try:
                    quote_dict['author']['username'] = quoted_msg_instance.author.username
                except:
                    quote_dict['author']['username'] = '???'
                try:
                    quote_dict['author']['name_color'] = quoted_msg_instance.author.profile.name_color
                except:
                    quote_dict['author']['name_color'] = '#FFFFFF'

                output_dict['quoted_message'] = quote_dict

        print(f"This will be sent as {output_dict}")

        self.send(text_data=json.dumps(output_dict))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'frontend',
            self.channel_name
        )
        
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

        ChatboxStateManager.delete_connected_user_with_id(self.user.id)

    def user_change(self, event):
        """
        This catches the 'user_change' type from the signal's group_send
        """
        print("dfopsjgpfvosrjgvjorj")
        self.send(text_data=json.dumps({
            'type': 'user_change',
            'message': event['message']
        }))