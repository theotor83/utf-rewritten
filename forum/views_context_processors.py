from .models import *
import random
from django.utils import timezone
from django.db.models import Count, Q

# The header_size variable is used to determine the size of the header image in the base template.
# It can be 'small' or 'big', depending on the context of the page being rendered.
# If it's neither, it defaults to 'big'.

# Context provider functions
# Naming convention: <theme_name>__<template>__processor
def modern__index__processor(request, base_context):
    online_users_qs = base_context["online"]
    
    online_data = organize_online_users_by_groups(online_users_qs)

    filter_list = ['normal', 'popular', 'newposts']
    index_filter = request.GET.get('filter', 'normal')
    if index_filter not in filter_list:
        index_filter = 'normal'
    print("Current filter:", index_filter)
    if index_filter == 'popular':
        print("Popular filter applied")
        filtered_topics = Topic.objects.select_related('author', 'author__profile', 'author__profile__top_group', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__author__profile__top_group', 'parent', 'category').prefetch_related('author__profile__groups', 'latest_message__author__profile__groups').filter(is_sub_forum=False).order_by('-total_views')[:100]
    elif index_filter == 'newposts':
        filtered_topics = Topic.objects.select_related('author', 'author__profile', 'author__profile__top_group', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__author__profile__top_group', 'parent', 'category').prefetch_related('author__profile__groups', 'latest_message__author__profile__groups').filter(is_sub_forum=False).order_by('-created_time')[:100]
    else:
        filtered_topics = None # This shouldn't display anyway

    return {
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
        'header_size': 'big',
        'index_filter': index_filter,
        'filtered_topics': filtered_topics,
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

    # TODO: [6] Add the last_login inside recent_activity
    recent_activity['this_month'] = Post.objects.filter(
        author=req_user,
        created_time__gte=now-timezone.timedelta(days=30)
    ).order_by('-created_time')
    recent_activity['last_month'] = Post.objects.filter(
        author=req_user,
        created_time__gte=now-timezone.timedelta(days=60),
        created_time__lte=now-timezone.timedelta(days=30)
    ).order_by('-created_time')

    all_posts = Post.objects.filter(author=req_user).order_by('-created_time')
    media_list = []
    for post in all_posts:
        add_img_to_list(post, media_list)

    return {
        'header_size': 'small',
        'user_is_online': user_is_online,
        'recent_activity': recent_activity,
        'topics_created': topics_created,
        'media_list': media_list,
    }


def modern__new_topic_form__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__subforum_details__processor(request, base_context):
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


def modern__new_post_form__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__search__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__search_results__processor(request, base_context):
    results = base_context.get('results', [])
    for result in results:
        result.author_is_online = result.author.profile.last_login >= timezone.now() - timezone.timedelta(minutes=30)
    return {
        'header_size': 'small',
        'results': results, # For avataronline / avataroffline display
    }


def modern__register__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__edit_profile__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__new_pm_form__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__new_pm_form_thread__processor(request, base_context):
    return {
        'header_size': 'small',
    }

def modern__category_details__processor(request, base_context):
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


def modern__topic_details__processor(request, base_context):
    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30)).order_by('username')
    online_data = organize_online_users_by_groups(online)
    utf = Forum.objects.filter(name='UTF').first()

    posts = base_context.get('posts', [])
    online_ids = [user.id for user in online]

    for post in posts:
        if post.author.id in online_ids:
            post.user_is_online = True

    all_posts = base_context.get('all_posts', [])
    participants = User.objects.filter(
        id__in=all_posts.values_list('author_id', flat=True)
    ).annotate(
        post_count=Count('posts', filter=Q(posts__in=all_posts))
    ).order_by('-post_count')

    return {
        'header_size': 'small',
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online': online,
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
        "utf": utf, # For _stats_header.html
        'posts': posts, # With user_is_online flag
        'participants': participants,
    }


def modern__group_details__processor(request, base_context):
    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30)).order_by('username')
    online_data = organize_online_users_by_groups(online)
    mods = base_context.get('mods', [])
    members = base_context.get('members', [])

    # Combine mods and members (modern doesn't display mods)
    group = base_context.get('group', None)
    members = list(members)
    for mod in mods:
        # If the mod is inside the group, add them to the member
        if group in mod.profile.groups.all():
            members.insert(0, mod) # Append at the top
    group_member_count = len(members)

    utf = Forum.objects.filter(name='UTF').first()
    total_count = Profile.objects.all().count()  # Total number of profiles in the forum
    return {
        'header_size': 'small',
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online': online,
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
        "utf": utf, # For _stats_header.html
        "members": members,
        "group_member_count": group_member_count,
        "total_count": total_count,
    }


def modern__pm_inbox__processor(request, base_context):
    return {
        'header_size': 'small',
    }


def modern__groups__processor(request, base_context):
    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30)).order_by('username')
    online_data = organize_online_users_by_groups(online)
    utf = Forum.objects.filter(name='UTF').first()

    all_groups = base_context.get('all_groups', [])
    for group in all_groups:
        # Get members and sort by their actual top group priority (using get_top_group method)
        members_list = list(Profile.objects.filter(groups=group).select_related('top_group').prefetch_related('groups'))
        # Sort by get_top_group priority (lowest first), then by last_login (latest first)
        members_list.sort(key=lambda profile: (
            profile.get_top_group.priority,  # Lowest priority first (ascending)
            -(profile.last_login or timezone.datetime.min.replace(tzinfo=timezone.timezone.utc)).timestamp()  # Latest last_login first (descending)
        ))
        group.members_overview = members_list[:5]

    member_count = utf.total_users
    return {
        'header_size': 'small',
        'recently_active_users': get_recently_active_users(12), # For _stats_header.html
        'online': online,
        'online_groups': online_data['groups'], # For _who_is_online.html
        'online_users_by_group': online_data['users_by_group'],
        'online_users_with_groups': online_data['structured_data'],
        "utf": utf, # For _stats_header.html
        'all_groups': all_groups,
        'member_count': member_count,
    }


def modern__pm_details__processor(request, base_context):
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
        'memberlist.html': modern__memberlist__processor,
        'profile_page.html': modern__profile_page__processor,
        'new_topic_form.html': modern__new_topic_form__processor,
        'subforum_details.html': modern__subforum_details__processor,
        'new_post_form.html': modern__new_post_form__processor,
        'search.html': modern__search__processor,
        'search_results.html': modern__search_results__processor,
        'register.html': modern__register__processor,
        'edit_profile.html': modern__edit_profile__processor,
        'new_pm_form.html': modern__new_pm_form__processor,
        'new_pm_form_thread.html': modern__new_pm_form_thread__processor,
        'topic_details.html': modern__topic_details__processor,
        'category_details.html': modern__category_details__processor,
        'group_details.html': modern__group_details__processor,
        'pm_inbox.html': modern__pm_inbox__processor,
        'groups.html': modern__groups__processor,
        'pm_details.html': modern__pm_details__processor,
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

def add_img_to_list(post, list):
    """Search for a images in the post.text and add it to the list.
      "https://utf-rewritten.org/media/archive/images/signalerimage-40a9961.png" and "https://utf-rewritten.org/media/archive/images/signalertext-40a8bad.png" must be excluded."""
    import re
    
    excluded_images = [
        "https://utf-rewritten.org/media/archive/images/signalerimage-40a9961.png",
        "https://utf-rewritten.org/media/archive/images/signalertext-40a8bad.png"
    ]
    
    # Regex patterns to match different image formats in the post text
    patterns = [
        # BBCode [img] tags: [img]url[/img] or [img=url]
        r'\[img\]([^[\]]+)\[/img\]',
        r'\[img=([^[\]]+)\]',
    ]
    
    # Search for images using all patterns
    for pattern in patterns:
        matches = re.finditer(pattern, post.text, re.IGNORECASE)
        for match in matches:
            # Get the image URL from the first capturing group
            image_url = match.group(1).strip()
            
            # Skip if it's in the excluded list
            if image_url not in excluded_images:
                # Add to list if not already present
                if image_url not in list:
                    list.append({"image_url": image_url, "post_id": post.id})  # Store image URL and post ID for reference
