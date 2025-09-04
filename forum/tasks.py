from celery import shared_task
from celery.exceptions import Retry
import logging
import os
from django.conf import settings

# Get or create logger
logger = logging.getLogger(__name__)

def safe_async_log(message, level='info', view_name=None):
    """
    Safely call async logging with fallback to synchronous logging if Celery fails.
    
    Args:
        message (str): The message to log
        level (str): Log level - 'debug', 'info', 'warning', 'error', 'critical'  
        view_name (str): Optional view name for context
    """
    # Format message with view name if provided
    if view_name:
        formatted_message = f"[{view_name}] {message}"
    else:
        formatted_message = message
    
    # In development mode, always print to console for immediate feedback
    if os.getenv('DEVELOPMENT_MODE', '').lower() in ['true', '1', 'yes']:
        level_upper = level.upper()
        print(f"[{level_upper}] {formatted_message}")
    
    try:
        # Try to send task to Celery
        async_log.delay(message, level, view_name)
    except Exception as e:
        # If Celery fails, log synchronously as fallback            
        # Add note about Celery failure in development
        if os.getenv('DEVELOPMENT_MODE', '').lower() in ['true', '1', 'yes']:
            fallback_message = f"{formatted_message} (Celery unavailable: {str(e)})"
        else:
            fallback_message = formatted_message
        
        # Log synchronously at the appropriate level
        if level.lower() == 'debug':
            logger.debug(fallback_message)
        elif level.lower() == 'info':
            logger.info(fallback_message)
        elif level.lower() == 'warning':
            logger.warning(fallback_message)
        elif level.lower() == 'error':
            logger.error(fallback_message)
        elif level.lower() == 'critical':
            logger.critical(fallback_message)
        else:
            # Default to info level
            logger.info(fallback_message)

@shared_task
def async_log(message, level='info', view_name=None):
    """
    Asynchronously log messages from views to avoid blocking.
    
    Args:
        message (str): The message to log
        level (str): Log level - 'debug', 'info', 'warning', 'error', 'critical'
        view_name (str): Optional view name for context
    """
    # Prefix with view name if provided
    if view_name:
        formatted_message = f"[{view_name}] {message}"
    else:
        formatted_message = message
    
    # Log at the appropriate level
    if level.lower() == 'debug':
        logger.debug(formatted_message)
    elif level.lower() == 'info':
        logger.info(formatted_message)
    elif level.lower() == 'warning':
        logger.warning(formatted_message)
    elif level.lower() == 'error':
        logger.error(formatted_message)
    elif level.lower() == 'critical':
        logger.critical(formatted_message)
    else:
        # Default to info level
        logger.info(formatted_message)
    
    return f"Logged: {formatted_message}"
