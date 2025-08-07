from .models import *
import random

# The header_size variable is used to determine the size of the header image in the base template.
# It can be 'small' or 'big', depending on the context of the page being rendered.
# If it's neither, it defaults to 'big'.

# Context provider functions
# Naming convention: <theme_name>__<template>__processor
def modern__index__processor(request, base_context):
    online_users_qs = base_context["online"]
    
    # Get online users grouped by their top group using prefetch_related for efficiency
    # TODO: [10] WARNING : Not all profiles have a top group set, so this might not work as expected. It should use get_top_group method instead.
    online_users_with_groups = online_users_qs.select_related('profile', 'profile__top_group').prefetch_related('profile__groups')
    
    # Create a dictionary to group online users by their top group
    online_users_by_group = {}
    online_groups = set()
    
    for user in online_users_with_groups:
        if user.profile:
            top_group = user.profile.get_top_group
            online_groups.add(top_group)
            
            if top_group not in online_users_by_group:
                online_users_by_group[top_group] = []
            online_users_by_group[top_group].append(user)
    
    # Convert set to ordered list (by priority)
    online_groups = sorted(online_groups, key=lambda g: g.priority, reverse=True)
    
    # Create a list of dictionaries for easier template access
    online_users_with_groups = [
        {
            'group': group,
            'users': online_users_by_group.get(group, [])
        }
        for group in online_groups
    ]
    
    print(f"Online top groups: {online_groups}")
    print(f"Users by group: {online_users_by_group}")
    print(f"Restructured data: {online_users_with_groups}")
    
    return {
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online_groups': online_groups,
        'online_users_by_group': online_users_by_group,  # Keep original for backwards compatibility
        'online_users_with_groups': online_users_with_groups,  # New structured data
        'header_size': 'big',
    }

def modern__faq__processor(request, base_context):
    return{
        'header_size': 'small',  # This will be used to set the header size in the base template
    }

def modern__register_regulation__processor(request, base_context):
    return {
        'header_size': 'small',
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
        'faq.html': modern__faq__processor,
        'register_regulation.html': modern__register_regulation__processor,
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