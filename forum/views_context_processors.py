from .models import *
import random

# Context provider functions
# Naming convention: <theme_name>__<template>__processor
def modern__index__processor(request, base_context):
    
    return {
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
    }

def test__index__processor(request, base_context):
    """Testing hello world context processor for the test theme."""
    
    return {
        'hello_world': 'Hello World, test',
    }





# Registry structure: theme: {template_filename: context_provider_function}
THEME_CONTEXT_REGISTRY = {
    'modern': {
        'index.html': modern__index__processor,
        # ... more views as needed
    },
    'test': {
        'index.html': test__index__processor,
        # ... more views as needed
    }
}





# Main function to get additional context
def get_theme_context(request, theme_name, base_context, template_name):
    """Use template name to identify which context provider to use"""
    theme_providers = THEME_CONTEXT_REGISTRY.get(theme_name, {})
    context_provider = theme_providers.get(template_name)
    
    if context_provider:
        try:
            return context_provider(request, base_context)
        except Exception as e:
            print(f"Error getting theme context: {e}")
            return {}
    else:
        return {}
    
# Helpers functions to be used elsewhere in the project
def get_recently_active_users(limit=12): # To be used in _stats_header.html 
    """Get a list of recently active users."""
    users = User.objects.select_related('profile').filter(profile__isnull=False).order_by('-last_login')[:limit]
    for user in users:
        user.profile.random_color = return_random_color(user.username)
    return users

def return_random_color(seed=None): # Used to generate random colors for user that don't have avatars
    """Return a random color in hex format."""
    if seed is not None:
        random.seed(seed)
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))