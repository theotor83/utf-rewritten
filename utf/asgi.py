# utf/asgi.py

"""
ASGI config for utf project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chatbox.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
	'http': django_asgi_app,
	'websocket': AuthMiddlewareStack(
		URLRouter(
			chatbox.routing.websocket_urlpatterns
		)
	)
})


if settings.DEBUG:
	application = ASGIStaticFilesHandler(application)
