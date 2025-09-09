# forum/middleware.py

import httpx
from django.conf import settings
import logging
import asyncio
from asgiref.sync import iscoroutinefunction
import threading

class ForceHTTPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        request._is_secure_override = True
        return self.get_response(request)

logger = logging.getLogger(__name__)

class WebhookMiddleware:
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        # Ensure the webhook URL is configured.
        if not settings.GET_WEBHOOK_URL:
            logger.warning("GET_WEBHOOK_URL is not set in the environment. Tracking will be disabled.")

    def __call__(self, request):
        # Check if we're in an async context
        
        if iscoroutinefunction(self.get_response):
            return self._async_call(request)
        else:
            return self._sync_call(request)

    def _sync_call(self, request):
        # Handle synchronous views
        response = self.get_response(request)
        
        # Fire webhook asynchronously without blocking
        self._fire_webhook_sync(request)
        
        return response

    async def _async_call(self, request):
        # Handle asynchronous views
        response = await self.get_response(request)
        
        # Fire webhook asynchronously
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
                        'username': f"{request.user.username}",
                        'content': f"🔔 **User Activity Alert**\n"
                                f"🌐 **Path:** {request.path}\n"
                                f"📍 **Method:** {request.method}\n"
                                f"🖥️ **User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]}...\n"
                                f"📡 **IP Address:** {request.META.get('REMOTE_ADDR', 'Unknown')}"
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
                'username': f"{request.user.username}",
                'content': f"🔔 **User Activity Alert**\n"
                          f"🌐 **Path:** {request.path}\n"
                          f"📍 **Method:** {request.method}\n"
                          f"🖥️ **User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]}...\n"
                          f"📡 **IP Address:** {request.META.get('REMOTE_ADDR', 'Unknown')}"
            }

            try:
                async with httpx.AsyncClient() as client:
                    await client.post(settings.GET_WEBHOOK_URL, json=payload, timeout=3.0)
            except httpx.RequestError as e:
                logger.error(f"Failed to send tracking data to webhook: {e}")