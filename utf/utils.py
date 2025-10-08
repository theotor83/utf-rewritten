"""
UTF-Rewritten utility functions
"""
import os
from django.conf import settings


def cprint(*args, **kwargs):
    """
    Conditional print function that respects DISABLE_CUSTOM_PRINTS setting.
    
    This function works exactly like Python's built-in print(), but only outputs
    to console if DISABLE_CUSTOM_PRINTS is False.
    
    Django's built-in logging and prints are not affected by this setting.
    
    Usage:
        from utf.utils import cprint
        cprint("Debug message")
        cprint(f"User {user_id} logged in")
    
    Args:
        *args: Variable length argument list (same as print())
        **kwargs: Arbitrary keyword arguments (same as print())
    """
    # Check if custom prints are disabled
    try:
        disable_prints = getattr(settings, 'DISABLE_CUSTOM_PRINTS', False)
    except:
        # If settings not loaded yet, check environment variable directly
        disable_prints = os.getenv('DISABLE_CUSTOM_PRINTS', 'False') == 'True'
    
    # Only print if custom prints are enabled
    if not disable_prints:
        print(*args, **kwargs)
