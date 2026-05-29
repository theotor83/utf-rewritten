class ChatboxSaveError(Exception):
    pass

class ChatboxMessageChecker:
    def __init__(self):
        pass

    def check_message(self, message) -> None:
        """
        Throws ValueError if message cannot be saved to database because it is malformed
        """
        try:
            self._verify_message_integrity(message)
            print("Message integrity check passed")
        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                raise ValueError(f"Message integrity check failed for unknown reasons: {e}")
            else:
                raise ChatboxSaveError(f"Message integrity check failed : {e}")

    def _verify_message_integrity(self, message):
        try:
            if not message:
                raise ChatboxSaveError("Message cannot be None")
            #if not message.id: # This is handled automatically by Django...
                #raise ChatboxSaveError("Message must have an ID")
            if not message.author:
                raise ChatboxSaveError("Message must have an author")
            if not message.text:
                raise ChatboxSaveError("Message must have text")
            #if not message.created_time: # Handled by Django too
                #raise ChatboxSaveError("Message must have a created time")
            if message.quoted_message and message.quoted_message.id == message.id:
                raise ChatboxSaveError("A message cannot quote itself.")
            # TODO [8]: Add a check for messages with weird dates (before 2015 and after current_year+1 or something)
            #if not message.text == "hot damn":
                #raise ChatboxSaveError("Message cannot be saved because it doesn't contain the phrase 'hot damn', which is not allowed for some reason, just kidding I know why it's not allowed it's just for testing.")

        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                print(f"Message integrity check failed for unchecked reason: {e}")
            raise ChatboxSaveError(f"Message integrity check failed : {e}")

    def _save_message_to_db(self, message):
        pass