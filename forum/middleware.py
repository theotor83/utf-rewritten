# forum/middleware.py

import asyncio
import inspect
import logging
import threading

import httpx
from asgiref.sync import async_to_sync
from django.conf import settings

class ForceHTTPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        request._is_secure_override = True
        response = self.get_response(request)
        if inspect.isawaitable(response):
            response = async_to_sync(self._await_response)(response)
        return response

    async def _await_response(self, awaitable_response):
        return await awaitable_response

logger = logging.getLogger(__name__)

class WebhookMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # Ensure the webhook URL is configured.
        if not settings.GET_WEBHOOK_URL:
            logger.warning("GET_WEBHOOK_URL is not set in the environment. Tracking will be disabled.")

    def __call__(self, request):
        response = self.get_response(request)
        if inspect.isawaitable(response):
            return async_to_sync(self._async_response_handler)(request, response)
        self._fire_webhook_sync(request)
        return response

    async def _async_response_handler(self, request, awaitable_response):
        response = await awaitable_response
        await self._fire_webhook_async(request)
        return response

    def _fire_webhook_sync(self, request):
        """Fire webhook in sync context using thread pool"""
        if settings.GET_WEBHOOK_URL and hasattr(request, 'user') and request.user.is_authenticated:
            
            def run_webhook():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    payload = {
                        'username': f"{request.user.username} (sync)",
                        'content': f"=================================================================\n"
                                f"👤**User:** {request.user.username}\n"
                                f"🌐 **Path:** {request.get_full_path()}\n"
                                f"📍 **Method:** {request.method}\n"
                                f"🖥️ **User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]}...\n"
                                f"📡 **IP Address:** {request.META.get('REMOTE_ADDR', 'Unknown')}\n"
                                f"🎨 **Theme:** {request.COOKIES.get('theme', 'None (Modern)')}\n"
                                f"=================================================================\n"
                    }
                    
                    async def send_webhook():
                        try:
                            async with httpx.AsyncClient() as client:
                                await client.post(settings.GET_WEBHOOK_URL, json=payload, timeout=3.0)
                        except httpx.RequestError as e:
                            logger.error(f"Failed to send tracking data to webhook: {e}")
                    
                    loop.run_until_complete(send_webhook())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error in webhook thread: {e}")
            
            # Start webhook in background thread
            webhook_thread = threading.Thread(target=run_webhook, daemon=True)
            webhook_thread.start()

    async def _fire_webhook_async(self, request):
        """Fire webhook in async context"""
        if settings.GET_WEBHOOK_URL and hasattr(request, 'user') and request.user.is_authenticated:
            payload = {
                'username': f"{request.user.username} (async)",
                'content': f"=================================================================\n"
                        f"👤**User:** {request.user.username}\n"
                        f"🌐 **Path:** {request.get_full_path()}\n"
                        f"📍 **Method:** {request.method}\n"
                        f"🖥️ **User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]}...\n"
                        f"📡 **IP Address:** {request.META.get('REMOTE_ADDR', 'Unknown')}\n"
                        f"🎨 **Theme:** {request.COOKIES.get('theme', 'None (Modern)')}\n"
                        f"=================================================================\n"
            }

            try:
                async with httpx.AsyncClient() as client:
                    await client.post(settings.GET_WEBHOOK_URL, json=payload, timeout=3.0)
            except httpx.RequestError as e:
                logger.error(f"Failed to send tracking data to webhook: {e}")