from django.core.cache import caches
from json import loads, dumps
import django.dispatch

user_change_signal = django.dispatch.Signal()

class ChatboxStateManager:
    """
    This class is responsible for managing the state of the chatbox.
    It manages things like connected users, room title, etc.

    connected_users will be stored like this:
    [
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
    """

    try:
        cache = caches['chatbox']
    except Exception as e:
        raise f"ChatboxStateManager could not get the correct cache layer : {e}"

    connected_users_key = 'connected_users' # This won't change

    @staticmethod
    def add_connected_user(user: dict):
        #print(f"[START] Adding user: {user}")
        if not user['id'] or not user['username'] or not user['name_color']:
            raise ValueError("User is not valid, missing a field")
        if ChatboxStateManager.is_user_connected(user['id']):
            print(f"User {user['id']} is already connected, skipping")
            return
        if not ChatboxStateManager._is_valid_hex_color(user['name_color']):
            raise ValueError("User name color is not a valid hex color")

        ChatboxStateManager._append_dict_to_cache_list(ChatboxStateManager.connected_users_key, user)
        #print(f"[END] Added user: {user}")

    @staticmethod
    def get_connected_users() -> list:
        connected_users =  ChatboxStateManager._get_cache_list(ChatboxStateManager.connected_users_key)
        #print(f"[WILL RETURN] Connected users: {connected_users}")
        return connected_users

    @staticmethod
    def delete_connected_user_with_id(user_id: int) -> bool:
        #print(f"[START] Removing user with id: {user_id}")
        connected_users = ChatboxStateManager.get_connected_users()

        for user in connected_users:
            if user['id'] == user_id:
                connected_users.remove(user)
                ChatboxStateManager._set_cache_list(ChatboxStateManager.connected_users_key, connected_users)
                print(f"Removed user with id: {user_id}")
                return True
        print(f"Could not find user with id: {user_id}")
        return False

    @staticmethod
    def is_user_connected(user_id: int) -> bool:
        connected_users = ChatboxStateManager.get_connected_users()

        for user in connected_users:
            if user['id'] == user_id:
                return True
        return False

    @staticmethod
    def _is_valid_hex_color(hex_color: str) -> bool:
        hex_color = hex_color.upper()
        if hex_color[0] != '#':
            return False
        hex_color = hex_color[1:]
        if len(hex_color) != 6:
            return False
        for char in hex_color:
            if char not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']:
                return False

        return True

    @staticmethod
    def _set_cache_list(key: str, list_value: list) -> None:
        """
        Sets the cache for the given key to the given list.
        """
        #print(f"[DEBUG] Will change the value of key: {key} to the list: {dumps(list_value)}")
        ChatboxStateManager.cache.set(key, dumps(list_value))
        print("Sending signal...")
        user_change_signal.send(sender=ChatboxStateManager, data=list_value) # Send the data as well

    @staticmethod
    def _append_dict_to_cache_list(key: str, dict_value: dict) -> None:
        #print(f"[DEBUG] Will append the dict: {dict_value} to the list in cache with key: {key}")
        list_in_cache = ChatboxStateManager._get_cache_list(key)
        list_in_cache.append(dict_value)
        #print(f"New cache list: {list_in_cache}")
        ChatboxStateManager._set_cache_list(key, list_in_cache)

    @staticmethod
    def _get_cache_list(key: str) -> list:
        #print(f"[DEBUG] Will get the list of cache: {key}")
        output_dict = []
        cache_value = ChatboxStateManager.cache.get(key)
        if cache_value:
            output_dict = loads(cache_value)

        return output_dict