from .models import *
import random
from django.utils import timezone

# The header_size variable is used to determine the size of the header image in the base template.
# It can be 'small' or 'big', depending on the context of the page being rendered.
# If it's neither, it defaults to 'big'.

# Context provider functions
# Naming convention: <theme_name>__<template>__processor
def modern__index__processor(request, base_context):
    online_users_qs = base_context["online"]
    
    online_data = organize_online_users_by_groups(online_users_qs)
    
    return {
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
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

def modern__memberlist__processor(request, base_context):
    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30)).order_by('username')
    online_data = organize_online_users_by_groups(online)
    utf = Forum.objects.filter(name='UTF').first()
    return {
        'header_size': 'small',
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online': online,
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
        "utf": utf, # For _stats_header.html
    }

def modern__profile_page__processor(request, base_context):
    user_is_online = False
    recent_activity = {"this_month":{}, 
                       "last_month":{} }

    now = timezone.now()
    req_user = base_context.get('req_user')

    if req_user and hasattr(req_user, 'profile') and req_user.profile and req_user.profile.last_login:
        user_is_online = now - req_user.profile.last_login <= timezone.timedelta(minutes=30)
    
    topics_created = Topic.objects.filter(author=req_user).filter(is_sub_forum=False).count()
    
    return {
        'header_size': 'small',
        'user_is_online': user_is_online,
        'recent_activity': recent_activity,
        'topics_created': topics_created,
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
        'memberlist.html': modern__memberlist__processor,
        'profile_page.html': modern__profile_page__processor,
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
    users = User.objects.select_related('profile').filter(profile__isnull=False).order_by('-profile__last_login')[:limit]
    for user in users:
        user.profile.random_color = return_random_color(user.username)
    return users

def return_random_color(seed=None): # Used to generate random colors for user that don't have avatars
    """Return a random color in hex format."""
    if seed is not None:
        random.seed(seed)
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def organize_online_users_by_groups(online_users_qs):
    """
    Organize online users by their top groups.
    
    Returns a dictionary with:
    - 'groups': List of groups ordered by priority
    - 'users_by_group': Dictionary mapping groups to their users  
    - 'structured_data': List of dicts with group and users for templates
    """
    # Get online users with their profile and group data
    # TODO: [10] WARNING : Not all profiles have a top group set, so this might not work as expected. It should use get_top_group method instead.
    online_users = online_users_qs.select_related('profile', 'profile__top_group').prefetch_related('profile__groups')
    
    # Group users by their top group
    users_by_group = {}
    all_groups = set()
    
    for user in online_users:
        if user.profile:
            top_group = user.profile.get_top_group
            all_groups.add(top_group)
            
            if top_group not in users_by_group:
                users_by_group[top_group] = []
            users_by_group[top_group].append(user)
    
    # Sort groups by priority (highest first)
    sorted_groups = sorted(all_groups, key=lambda g: g.priority, reverse=True)
    
    # Create template-friendly structure
    structured_data = []
    for group in sorted_groups:
        structured_data.append({
            'group': group,
            'users': users_by_group.get(group, [])
        })
    
    return {
        'groups': sorted_groups,
        'users_by_group': users_by_group,
        'structured_data': structured_data
    }