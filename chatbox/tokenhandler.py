class TokenHandler:
    def __init__(self):
        pass

    def get_token_from_str_token(self, token):
        from rest_framework.authtoken.models import Token # Here because it needs to be imported last, or else we get a "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet." error.
        try:
            return Token.objects.get(key=token)
        except Token.DoesNotExist:
            return None

    def get_token_from_user(self, user):
        from rest_framework.authtoken.models import Token
        try:
            return Token.objects.get(user=user)
        except Token.DoesNotExist:
            return None

    def get_user_instance_from_token(self, token):
        token_instance = self._return_token_polymorphic(token)

        if not token_instance:
            return None

        try:
            return token_instance.user
        except Exception as e:
            print(f"Error getting user instance from token: {e}")
        return None

    def get_username_from_token(self, token):
        token_instance = self._return_token_polymorphic(token)

        if not token_instance:
            return None

        try:
            return token_instance.user.username
        except Exception as e:
            print(f"Error getting username from token: {e}")
        return None

    def get_name_color_from_token(self, token):
        token_instance = self._return_token_polymorphic(token)
        if not token_instance:
            return None

        try:
            return token_instance.user.profile.name_color
        except Exception as e:
            print(f"Error getting name color from token: {e}")
        return None

    def get_user_id_from_token(self, token):
        token_instance = self._return_token_polymorphic(token)

        if not token_instance:
            return None

        try:
            return token_instance.user.id
        except Exception as e:
            print(f"Error getting user id from token: {e}")
        return None

    # TODO [9]: Also add methods to get the top_group dict and all its attributes :
    # "top_group": {
 	#		"id": 10,
    #		"name": "Determination",
    #		"color": "#C02200"
    #   }

    def get_user_dict(self, token):
        return {
            'username': self.get_username_from_token(token),
            'name_color': self.get_name_color_from_token(token),
        }

    def _return_token_polymorphic(self, token):
        from rest_framework.authtoken.models import Token

        token_instance = None

        if isinstance(token, str):
            token_instance = self.get_token_from_str_token(token)
        elif isinstance(token, Token):
            token_instance = token
        if not token_instance:
            return None
        return token_instance