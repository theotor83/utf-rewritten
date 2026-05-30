from datetime import date

class ChatboxSaveError(Exception):
    pass

class ChatboxMessageChecker:
    def __init__(self):
        pass

    def check_message_pre_save(self, message) -> None:
        """
        Throws ChatboxSaveError if message is malformed, and ValueError if there is an unknown error.
        Only deals with pre-save status, meaning things like auto-incremented IDs and created times are ignored and need to be
        checked after Django saved them, and rollback if needed.
        """
        try:
            self._verify_message_integrity(message)
            print("Message integrity check passed")
        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                raise ValueError(f"Message integrity check failed for unknown reasons: {e}")
            else:
                raise ChatboxSaveError(f"Message integrity check failed : {e}")

    def check_message_post_save(self, message) -> None:
        """
        Throws ChatboxSaveError if some fields are malformed, and ValueError if there is an unknown error.
        Only deals with post-save status, which are things like auto-incremented IDs and created times, that Django handles automatically.
        """
        try:
            self._verify_message_saved_correctly(message)
            print("Message post-save check passed")
        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                raise ValueError(f"Message post-save check failed for unknown reasons: {e}")
            else:
                raise ChatboxSaveError(f"Message post-save check failed : {e}")


    def _verify_message_integrity(self, message):
        try:
            if not message:
                raise ChatboxSaveError("Message cannot be None")
            if not message.author:
                raise ChatboxSaveError("Message must have an author")
            if not message.text:
                raise ChatboxSaveError("Message must have text")
            if message.quoted_message and message.quoted_message.id == message.id:
                raise ChatboxSaveError("A message cannot quote itself.")

        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                print(f"Message integrity check failed for unchecked reason: {e}")
            raise ChatboxSaveError(f"Message integrity check failed : {e}")

    def _verify_message_saved_correctly(self, message):
        try:
            current_year = date.today().year # I hope this is safe..?
            if not message.id:
                raise ChatboxSaveError("Message must have an ID")
            if not message.created_time:
                raise ChatboxSaveError("Message must have a created time")
            if message.quoted_message and message.quoted_message.id == message.id:
                raise ChatboxSaveError("A message cannot quote itself.")
            if message.created_time.year < 2015 or message.created_time.year > current_year+1: # To be very generous... Weird things can still happen, but at least they would be funny
                raise ChatboxSaveError(f"Message created_time is invalid : {message.created_time}")

        except Exception as e:
            if not isinstance(e, ChatboxSaveError):
                print(f"Message post-save check failed for unchecked reason: {e}")
            raise ChatboxSaveError(f"Message post-save check failed : {e}")