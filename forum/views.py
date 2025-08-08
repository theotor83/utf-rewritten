# forum/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, ProfileForm, NewTopicForm, NewPostForm, QuickReplyForm, MemberSortingForm, UserEditForm, RecentTopicsForm, RecentPostsForm, PollForm, PollVoteFormUnique, PollVoteFormMultiple, NewPMThreadForm, NewPMForm
from .models import Profile, ForumGroup, User, Category, Post, Topic, Forum, TopicReadStatus, SmileyCategory, Poll, PollOption, PrivateMessageThread, PrivateMessage
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db import models
from django.db.models import Case, When, Value, BooleanField, Q, Count, F, OuterRef, Subquery
from django.db.models.functions import Lower
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from precise_bbcode.models import SmileyTag
from .views_context_processors import get_theme_context
from utf.settings import THEME_LIST, DEFAULT_THEME

# Functions used by views

def generate_pagination(current_page, max_page):
    if max_page == 1:
        return [1]
    
    first_part = [1, 2, 3] if max_page >= 3 else []
    last_part = [max_page - 2, max_page - 1, max_page] if max_page >= 3 else []
    
    middle_part = []
    for p in [current_page - 1, current_page, current_page + 1]:
        if 1 <= p <= max_page:
            middle_part.append(p)
    
    pages = sorted(set(first_part + middle_part + last_part))
    
    pagination = []
    prev = None
    for page in pages:
        if prev is not None and page > prev + 1:
            pagination.append("...")
        pagination.append(page)
        prev = page
    
    return pagination

def check_subforum_unread(subforum, user, depth=0, max_depth=10):
    """
    Check if any child topic in a subforum is unread by the user.
    
    Args:
        subforum: The subforum to check
        user: The current user
        depth: Current recursion depth (to prevent infinite loops)
        max_depth: Maximum recursion depth to prevent stack overflow
    
    Returns:
        Boolean indicating if the subforum contains any unread content
    """
    # Safety check to prevent infinite recursion
    if depth > max_depth:
        return False
        
    if not user.is_authenticated:
        return False
    
    # Get all direct child topics of this subforum
    child_topics = subforum.children.all()
    
    if not child_topics.exists():
        return False
    
    # Get read statuses for these topics in bulk
    read_statuses = TopicReadStatus.objects.filter(
        user=user,
        topic__in=child_topics
    ).values('topic_id', 'last_read')
    
    # Build a lookup dictionary {topic_id: last_read_time}
    read_status_map = {rs['topic_id']: rs['last_read'] for rs in read_statuses}
    
    # Check each child topic
    for topic in child_topics:
        # If the topic is a subforum, check it recursively
        if getattr(topic, 'is_sub_forum', False):
            if check_subforum_unread(topic, user, depth + 1, max_depth):
                return True
        else:
            # For regular topics, check its read status
            last_read = read_status_map.get(topic.id)
            if not last_read:  # Never read
                return True
            if topic.last_message_time > last_read:
                return True
    
    return False

def get_percentage(small, big):
    try:
        return round((small / big) * 100.0, 2) if big != 0 else 0
    except ZeroDivisionError:
        return 0

def get_message_frequency(message_count, date_joined, date_now=None):
    if date_now is None:
        date_now = timezone.now()
    
    # Ensure date_joined is timezone-aware
    if date_joined.tzinfo is None:
        raise ValueError("date_joined must be timezone-aware")
    
    # Calculate the number of days since the user joined
    days_since_joining = (date_now - date_joined).days
    
    if days_since_joining < 0:
        return "0 mess. tous les 0 jours"
    if days_since_joining == 0:
        return f"{message_count} mess. tous les 1 jours"
    
    # Calculate messages per day (average)
    if message_count <= 0:
        return "0 mess. tous les 1 jours"
    
    day_number = max(1, round(days_since_joining / message_count))
    
    return f"{max(1, message_count // (days_since_joining // day_number))} mess. tous les {day_number} jours"

def get_post_page_in_topic(post_id, topic_id, posts_per_page=15):
    try:
        post = Post.objects.get(id=post_id, topic_id=topic_id)
        topic = post.topic
        relative_position = topic.replies.filter(created_time__lte=post.created_time).count()
        print(f"Relative position: {relative_position}")
        page_number = (relative_position // posts_per_page) + 1
        return page_number
    except Post.DoesNotExist:
        return None
    
def mark_all_topics_read_for_user(user):
    """Mark all topics as read for the user."""
    if not user.is_authenticated:
        return

    # Get all topics in the forum
    all_topics = Topic.objects.all()

    # Iterate through each topic and mark it as read for the user
    for topic in all_topics:
        TopicReadStatus.objects.update_or_create(
            user=user,
            topic=topic,
            defaults={'last_read': timezone.now()}
        )

# TODO: [2] Make the filter recursive for nested subforums
def mark_as_read_with_filter(user, filter_dict):
    """Mark all topics as read for the user."""
    if not user.is_authenticated:
        return
    
    subforum = filter_dict.get('subforum')
    if not subforum:
        subforum = -1
    else:
        if not subforum.isnumeric():
            subforum = -1
        else:
            subforum = int(subforum)
    
    category = filter_dict.get('category')
    if not category:
        category = -1
    else:
        if not category.isnumeric():
            category = -1
        else:
            category = int(category)

    # Get topics according to the filter
    if subforum != -1:
        topics = Topic.objects.filter(parent=subforum)

    elif category != -1:
        topics = Topic.objects.filter(category=category)

    else: # If no filter is provided, return False (for error handling)
        return False

    if topics.count() == 0: # For error handling, if no topics are found
        return False
    # Iterate through each topic and mark it as read for the user
    for topic in topics:
        TopicReadStatus.objects.update_or_create(
            user=user,
            topic=topic,
            defaults={'last_read': timezone.now()}
        )
        print(f"Marked topic {topic.id} as read for user {user.username}")
    
    # Return True if topics were marked as read
    return True

def user_can_vote(user, poll):
    """Check if the user can vote in the poll, assuming users can't change their votes."""

    if not user.is_authenticated:
        return False
    
    if poll.is_active == False:
        return False

    # Check if the user has voted in the poll
    return not poll.options.filter(voters=user).exists()

def theme_render(request, template_name, context=None, content_type=None, status=None, using=None):
    if not THEME_LIST:
        raise ValueError("THEME_LIST is empty. Please define at least one theme in settings.py.")
    if DEFAULT_THEME:
        theme = DEFAULT_THEME
    else:
        theme = THEME_LIST[0]
        print(f"WARNING: DEFAULT_THEME is not set. Using the first value of THEME_LIST ({THEME_LIST[0]}) as fallback.")
        
    if context is None:
        context = {}

    theme = request.COOKIES.get('theme', DEFAULT_THEME)
    if theme is None or theme not in THEME_LIST: # Default theme fallback
        theme = DEFAULT_THEME

    # Use template name as identifier
    additional_context = get_theme_context(request, theme, context, template_name)
    
    enhanced_context = {**context, **additional_context}

    # Render the template with the theme
    return render(request, f"themes/{theme}/{template_name}", enhanced_context, content_type, status, using)

# Create your views here.

def index_redirect(request):
    return redirect("index")

@ratelimit(key='user_or_ip', method=['GET'], rate='5/10s')
@ratelimit(key='user_or_ip', method=['GET'], rate='200/h')

@ratelimit(key='user_or_ip', method=['POST'], rate='3/5m')
def index(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    categories = Category.objects.filter(is_hidden=False)
    timezone_now = timezone.now()
    
    # Process topics for each category
    for category in categories:
        # Get topics but don't use the queryset directly
        topics_list = list(category.index_topics.select_related('latest_message').prefetch_related('children').all().order_by('id')) # order by id for some reason idk
        
        # If user is authenticated, check read status for all topics
        if request.user.is_authenticated:
            # Get all topic IDs
            topic_ids = [topic.id for topic in topics_list]
            
            # Get all read statuses in one query
            read_statuses = TopicReadStatus.objects.filter(
                user=request.user,
                topic_id__in=topic_ids
            ).values('topic_id', 'last_read')
            
            # Create a lookup dictionary for quick access
            read_status_map = {rs['topic_id']: rs['last_read'] for rs in read_statuses}
            
            # Attach is_unread to each topic object
            for topic in topics_list:
                if getattr(topic, 'is_sub_forum', False):
                    # For subforums, check if any child is unread
                    # Pass in the topic as the subforum to check
                    topic.is_unread = check_subforum_unread(topic, request.user)
                else:
                    # For regular topics, check its own read status
                    last_read = read_status_map.get(topic.id)
                    if not last_read:
                        topic.is_unread = True  # Never read
                    else:
                        topic.is_unread = topic.last_message_time > last_read
        else:
            # If user is not authenticated, mark all topics as read
            for topic in topics_list:
                topic.is_unread = False
        
        # Store the processed list directly on the category
        category.processed_topics = topics_list

    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30)).order_by('username')

    groups = ForumGroup.objects.all()

    try:
        presentations = Topic.objects.filter(is_sub_forum=True, title="Présentations").first()
    except Topic.DoesNotExist:
        presentations = None
    try:
        regles = Topic.objects.filter(is_sub_forum=False, is_announcement=True).first()
    except Topic.DoesNotExist:
        regles = None

    today = timezone_now.date()
    next_week = today + timezone.timedelta(days=7)

    birthdays_today = User.objects.filter(
        profile__birthdate__day=today.day,
        profile__birthdate__month=today.month
    ).order_by('username')

    if today.month == next_week.month:
        birthdays_in_week = User.objects.filter(
            profile__birthdate__month=today.month,
            profile__birthdate__day__gte=today.day,
            profile__birthdate__day__lte=next_week.day
        ).order_by('username')
    else:
        birthdays_in_week = User.objects.filter(
            Q(profile__birthdate__month=today.month, profile__birthdate__day__gte=today.day) |
            Q(profile__birthdate__month=next_week.month, profile__birthdate__day__lte=next_week.day)
        ).order_by('username')

    # Quick access
    recent_posts = Post.objects.select_related('author', 'topic').filter(topic__is_sub_forum=False).order_by('-created_time')[:6]

    recent_topic_with_poll = Topic.objects.filter(poll__isnull=False).order_by('-created_time').first()

    print(recent_topic_with_poll)

    context = {
        "categories": categories,
        "utf":utf,
        "online":online,
        "form": form,
        "groups":groups,
        "presentations":presentations,
        "regles":regles,
        "birthdays_today":birthdays_today,
        "birthdays_in_week":birthdays_in_week,
        "recent_posts": recent_posts,
        "recent_topic_with_poll": recent_topic_with_poll,
        "timezone_now": timezone_now,
    }

    return theme_render(request, "index.html", context)

def faq(request):
    return theme_render(request, "faq.html")

def register_regulation(request):
    return theme_render(request, "register_regulation.html")

@ratelimit(key='user_or_ip', method=['POST'], rate='3/h')
@ratelimit(key='user_or_ip', method=['POST'], rate='5/d')
def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save User first
            user = user_form.save()
            
            # Save Profile linked to the User
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            try:
                outsider_group = ForumGroup.objects.get(name="Outsider")
                profile.groups.add(outsider_group)
            except ForumGroup.DoesNotExist:
                return HttpResponse(status=500)
            login(request, user)
            return redirect('index')
    else:
        user_form = UserRegisterForm()
        profile_form = ProfileForm()

    context = {'user_form': user_form, 'profile_form': profile_form}
    return theme_render(request, 'register.html', context)

def error_page(request, error_title, error_message, status=500):
    context = {"error_title":error_title, "error_message":error_message, "status":status}
    return theme_render(request, "error_page.html", context, status=status)

@ratelimit(key='user_or_ip', method=['POST'], rate='10/5m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/12h')
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    context = {'form': form}
    return theme_render(request, "login.html", context)

def logout_view(request):
    logout(request)
    return redirect("index")

@ratelimit(key='user_or_ip', method=['GET'], rate='5/5s')
def profile_details(request, userid):
    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    try :
        requested_user = User.objects.get(id=userid)
    except:
        return error_page(request, "Informations", "Désolé, mais cet utilisateur n'existe pas.", status=404)
    
    percentage = get_percentage(requested_user.profile.messages_count, utf.total_messages)
    context = {"req_user":requested_user, "percentage":percentage, "message_frequency":get_message_frequency(requested_user.profile.messages_count, requested_user.date_joined)}
    return theme_render(request, "profile_page.html", context)
    
@ratelimit(key='user_or_ip', method=['GET'], rate='10/30s')
def member_list(request):
    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page
    all_members = User.objects.select_related('profile').filter(profile__isnull=False).order_by('-id')
    count = all_members.count()
    max_page = (count + members_per_page - 1) // members_per_page

    pagination = generate_pagination(current_page, max_page)

    if request.method == 'POST':
        form = MemberSortingForm(request.POST)
        if form.is_valid():
            mode = form.cleaned_data['mode']
            order = form.cleaned_data['order']
            
            # Redirect to a URL with the parameters (e.g., same page)
            params = urlencode({'mode': mode, 'order': order})
            return redirect(f"{reverse('member-list')}?{params}")
    else:
        form = MemberSortingForm(request.GET or None)
        mode = request.GET.get('mode', 'joined')
        order = request.GET.get('order', 'ASC')

        custom_filter = None
        order_by_field = None
        members = None

        if mode == "joined":
            order_by_field = "id"
        elif mode == "lastvisit":
            order_by_field = "profile__last_login"
        elif mode == "username":
            order_by_field = "lower_username"
        elif mode == "posts":
            order_by_field = "profile__messages_count"
        elif mode == "email":
            custom_filter = {"profile__email_is_public": True}
            order_by_field = "id"
        elif mode == "website":
            custom_filter = {"profile__website__isnull": False}
            order_by_field = "id"
        elif mode == "topten":
            # Always get top 10 posters regardless of pagination
            members = User.objects.select_related('profile').filter(profile__isnull=False).order_by('-profile__messages_count')[:10]  # Descending order + limit 10
            # Disable pagination for top10 mode
            pagination = []

        # Apply ordering before slicing
        if order == "DESC":
            order_by_field = f"-{order_by_field}"  # Prefix with '-' for descending order
        
        if members is None:
            # Only apply pagination for non-topten modes
            if custom_filter is not None and mode != "username":
                members = User.objects.select_related('profile').filter(profile__isnull=False, **custom_filter).order_by(order_by_field)[limit - members_per_page : limit]
            elif custom_filter is not None and mode == "username":
                members = User.objects.annotate(lower_username=Lower('username')).select_related('profile').filter(profile__isnull=False, **custom_filter).order_by("lower_username")[limit - members_per_page : limit]
            elif custom_filter is None and mode != "username":
                members = User.objects.select_related('profile').filter(profile__isnull=False).order_by(order_by_field)[limit - members_per_page : limit]
            elif custom_filter is None and mode == "username":
                members = User.objects.annotate(lower_username=Lower('username')).select_related('profile').filter(profile__isnull=False).order_by(order_by_field)[limit - members_per_page : limit]



    context =  {
        "members" : members,
        "current_page" : current_page,
        "max_page":max_page,
        "pagination":pagination,
        "form":form,
        "count":count,
    }

    return theme_render(request, "memberlist.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='50/5s')
def subforum_details(request, subforumid, subforumslug):
    try:
        subforum = Topic.objects.select_related('category').get(id=subforumid)
    except:
        error_page(request,"Erreur","jsp")

    if request.method == 'POST':
        form = RecentTopicsForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            
            # Redirect to a URL with the parameters (e.g., same page)
            params = urlencode({'days': days})
            return redirect(f"{reverse('subforum-details', args=[subforumid, subforumslug])}?{params}")
    
    else:
        form = RecentTopicsForm(request.GET or None)

    days = int(request.GET.get('days', 0))
    topics_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * topics_per_page
    all_topics = subforum.children.select_related('author', 'author__profile', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__topic').filter(is_sub_forum=False)
    all_subforums = Topic.objects.select_related('category', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__topic').filter(parent=subforum, is_sub_forum=True)
    announcement_topics = Topic.objects.select_related('author', 'author__profile', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__topic', 'poll').filter(is_announcement=True)
    count = all_topics.count()
    max_page = (count + topics_per_page - 1) // topics_per_page

    if days > 0:
        # Filter topics based on the number of days
        date_threshold = timezone.now() - timezone.timedelta(days=days)
        all_topics = all_topics.filter(last_message_time__gte=date_threshold)

    topics = all_topics.order_by('-is_pinned', '-last_message_time')[limit - topics_per_page : limit]

    pagination = generate_pagination(current_page, max_page)

    tree = subforum.get_tree

    if request.user.is_authenticated:
        read_statuses = TopicReadStatus.objects.filter(
            user=request.user,
            topic__in=topics
        )
        read_status_map = {rs.topic_id: rs.last_read for rs in read_statuses}
        for topic in topics:
            if topic.is_sub_forum:
                topic.is_unread = topic.check_subforum_unread(request.user)
            else:
                topic.user_last_read = read_status_map.get(topic.id, None)
    else:
        for topic in topics:
            topic.user_last_read = None

    if request.user.is_authenticated:
        read_statuses_ann = TopicReadStatus.objects.filter(
            user=request.user,
            topic__in=announcement_topics
        )
        read_status_map_ann = {rs.topic_id: rs.last_read for rs in read_statuses_ann}
        for announcement in announcement_topics:
            if announcement.is_sub_forum:
                announcement.is_unread = check_subforum_unread(announcement, request.user)
            else:
                announcement.user_last_read = read_status_map_ann.get(announcement.id, None)
    else:
        for announcement in announcement_topics:
            announcement.user_last_read = None

    context = {"announcement_topics":announcement_topics,
                "topics":topics,
                "subforum":subforum,
                "tree":tree,
                "all_subforums":all_subforums,
                "form":form,
                "pagination":pagination,
                "current_page":current_page,
                "max_page":max_page,} 
    return theme_render(request, 'subforum_details.html', context)

def test_page(request):
    return theme_render(request, "search.html")

@ratelimit(key='user_or_ip', method=['POST'], rate='3/3m')
@ratelimit(key='user_or_ip', method=['POST'], rate='50/d')
def new_topic(request):
    if 'f' in request.GET and not 'c' in request.GET:
        subforum_id = request.GET.get('f')
        subforum = Topic.objects.get(id=subforum_id)
        if subforum == None:
            return error_page(request, "Erreur", "Le sous-forum n'a pas été trouvé.", status=404)
        if subforum.is_sub_forum == False:
            return error_page(request, "Erreur", "Vous ne pouvez pas créer de sujet ici.", status=403)

        tree = subforum.get_tree

        if request.user.is_authenticated == False:
            return redirect("login-view")
        else:
            if subforum.title != "Présentations":
                try:
                    user_profile = Profile.objects.get(user=request.user)
                    user_groups = user_profile.groups.all()
                    # Check if the user has no group
                    if user_groups.count() == 0:
                        return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
                    else:
                        # Check if the user is "Outsider" as top group
                        top_group = user_profile.get_top_group
                        if top_group.name == "Outsider":
                            return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
                except Profile.DoesNotExist:
                    return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
            if subforum.is_locked and request.user.profile.is_user_staff == False:
                return error_page(request, "Informations", "Vous ne pouvez pas créer de sujet ici.", status=403)

        if request.method == 'POST':
            form = NewTopicForm(request.POST, user=request.user, subforum=subforum)
            poll_form = PollForm(request.POST)
            
            poll_intended = bool(request.POST.get('question')) # Check if a poll was attempted

            form_is_valid = form.is_valid()
            poll_form_is_valid = True # Assume valid if no poll intended

            if poll_intended:
                poll_form_is_valid = poll_form.is_valid()

            if form_is_valid and poll_form_is_valid:
                new_topic_instance = form.save(commit=True) # Save the topic and its initial post

                if poll_intended:
                    # Create and save the Poll instance
                    poll_instance = Poll.objects.create(
                        topic=new_topic_instance,
                        question=poll_form.cleaned_data['question'],
                        days_to_vote=poll_form.cleaned_data['days_to_vote'],
                        max_choices_per_user=poll_form.cleaned_data['multiple_choice'],
                        can_change_vote=poll_form.cleaned_data['can_change_vote'],
                    )
                    # Create PollOption instances
                    for option_text in poll_form.cleaned_data['options']:
                        PollOption.objects.create(poll=poll_instance, text=option_text)
                
                return redirect(topic_details, new_topic_instance.id, new_topic_instance.slug)

        else: # GET request
            form = NewTopicForm(user=request.user, subforum=subforum)
            poll_form = PollForm()

        smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

        context = {
            'form': form, 
            'subforum': subforum, 
            'tree':tree,
            'smiley_categories': smiley_categories,
            'poll_form': poll_form,
        }

    elif 'c' in request.GET and not 'f' in request.GET:
        category_id = request.GET.get('c')
        category = Category.objects.get(id=category_id)
        if category == None:
            return error_page(request, "Erreur", "La catégorie n'a pas été trouvée.", status=404)

        tree = {}

        if request.user.is_authenticated == False:
            return redirect("login-view")
        else:
            try:
                user_profile = Profile.objects.get(user=request.user)
                user_groups = user_profile.groups.all()
                # Check if the user has no group
                if user_groups.count() == 0:
                    return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
                else:
                    # Check if the user is "Outsider" as top group
                    top_group = user_profile.get_top_group
                    if top_group.name == "Outsider":
                        return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
            except Profile.DoesNotExist:
                return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.", status=403)
            #if category.is_locked and request.user.profile.is_user_staff == False:
            #    return error_page(request, "Informations", "Vous ne pouvez pas créer de sujet ici.")

        if request.method == 'POST':
            form = NewTopicForm(request.POST, user=request.user, subforum=category)
            if form.is_valid():
                new_topic = form.save()
                return redirect(topic_details, new_topic.id, new_topic.slug)
        else:
            form = NewTopicForm(user=request.user, subforum=category)
            poll_form = PollForm()

        smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

        context = {
            'form': form, 
            'category': category, 
            'tree':tree,
            'smiley_categories': smiley_categories,
            'poll_form': poll_form,
        }


    return theme_render(request, 'new_topic_form.html', context)

@ratelimit(key='user_or_ip', method=['POST'], rate='8/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='200/d')
def topic_details(request, topicid, topicslug):
    print(f"[DEBUG] Entered topic_details view for topicid={topicid}, topicslug={topicslug}, method={request.method}")
    try:
        topic = Topic.objects.select_related('poll', 'author', 'author__profile').get(id=topicid)        
        print(f"[DEBUG] Topic found: {topic}")
        if request.user.is_authenticated:
            print(f"[DEBUG] User is authenticated: {request.user}")
            read_status, createdBool = TopicReadStatus.objects.get_or_create(user=request.user, topic=topic) # Get the read status for the topic, before updating
            print(f"[DEBUG] TopicReadStatus: {read_status}, created: {createdBool}")
            if createdBool == False: # If the read status already exists, check if it has been 3 minutes since the last read
                if read_status.last_read + timezone.timedelta(minutes=3) < timezone.now():
                    current = topic
                    while current != None: # Check if the topic is a subforum, and if so, get the parent topic
                        current.total_views += 1 # Increment the topic views
                        current.save(update_fields=["total_views"])
                        print(f"[DEBUG] Incremented total_views for topic {current.id}, now {current.total_views}")
                        current = current.parent # Go to the parent topic
            else: # Else, always increment the topic views
                current = topic
                while current != None: # Check if the topic is a subforum, and if so, get the parent topic
                    current.total_views += 1 # Increment the topic views
                    current.save(update_fields=["total_views"])
                    print(f"[DEBUG] Incremented total_views for topic {current.id}, now {current.total_views}")
                    current = current.parent # Go to the parent topic
            TopicReadStatus.objects.update_or_create( user=request.user, topic=topic, defaults={'last_read': timezone.now()})  # Mark the topic as read for the user
    except Topic.DoesNotExist as e:
        print(f"[ERROR] Topic.DoesNotExist: {e}")
        return error_page(request, "Erreur", "Ce sujet n'existe pas.", status=404)

    subforum = topic.parent

    posts_per_page = min(int(request.GET.get('per_page', 15)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * posts_per_page
    all_posts = Post.objects.select_related('author', 'author__profile', 'author__profile__top_group').filter(topic=topic)
    count = all_posts.count()
    max_page = (count + posts_per_page - 1) // posts_per_page
    days = int(request.GET.get('days', 0))
    order = request.GET.get('order', 'ASC')

    # Order before slicing
    if order == "DESC":
        all_posts = all_posts.reverse()

    if days > 0:
        # Filter topics based on the number of days
        date_threshold = timezone.now() - timezone.timedelta(days=days)
        all_posts = all_posts.filter(created_time__gte=date_threshold)

    # Slice the posts for pagination
    posts = all_posts.order_by('created_time')[limit - posts_per_page : limit]

    if posts.count() == 0:
        print(f"[DEBUG] No posts found for topic {topic.id}")
        return error_page(request, "Informations","Il n'y a pas de messages.", status=404)

    pagination = generate_pagination(current_page, max_page)

    tree = topic.get_tree
    # for i in tree:
    #     print(f" tree : {tree}")
    
    #if posts.count() <= 0:
    #    return error_page(request, "Erreur","Ce sujet n'a pas de messages.")
    has_poll = hasattr(topic, 'poll')
    poll_vote_form = None
    user_can_vote_bool = False # Default to False to avoid errors if poll_vote_form is None
    user_has_voted = 0
    poll_options = None

    if has_poll:
        poll = topic.poll
        print(f"[DEBUG] Poll found for topic {topic.id}: {poll}")

        poll_options = PollOption.objects.prefetch_related('voters').filter(poll=topic.poll).order_by('id')
        # Get the total vote count for the poll once (We can use the poll's related manager for this.)
        total_poll_votes = poll.options.aggregate(
            total=Count('voters')
        )['total'] or 0
        # Annotate each option with its vote count (only one query)
        poll_options = poll.options.annotate(
            vote_count=Count('voters')
        ).order_by('id')
        # Add percentage and bar length to each option object
        for option in poll_options:
            option.vote_count = option.vote_count  # The annotated value
            if total_poll_votes > 0:
                percentage = int((option.vote_count / total_poll_votes) * 100)
            else:
                percentage = 0
            option.percentage = percentage
            if percentage > 0:
                option.bar_length = int(2 * percentage + (0.05 * 2 * percentage))
            else:
                option.bar_length = 0
                
        # Check if the user has already voted in the poll
        if request.user.is_authenticated:
            user = request.user
            if poll.has_user_voted(user):
                print(f"[DEBUG] User {user.username} has already voted in poll {poll.id}")
                user_has_voted = 1
            else:
                print(f"[DEBUG] User {user.username} has NOT voted in poll {poll.id}")
                user_has_voted = 0
    
        if request.method == 'POST' and 'submit_vote_button' in request.POST:
            print(f"[DEBUG] Poll vote POST detected. Request POST data: {request.POST}")
            if request.POST.get('vote') == '1':
                # Determine which form class to use
                if topic.poll.allow_multiple_choices:
                    CurrentPollVoteForm = PollVoteFormMultiple
                    print("[DEBUG] Using PollVoteFormMultiple") # Debug print
                else:
                    CurrentPollVoteForm = PollVoteFormUnique
                    print("[DEBUG] Using PollVoteFormUnique") # Debug print

                poll_vote_form = CurrentPollVoteForm(request.POST, poll_options=topic.poll.options.all())
                #print(f"[DEBUG] PollVoteForm instantiated: {poll_vote_form}")
            else:
                print(f"[DEBUG] 'vote' not '1' in POST: {request.POST.get('vote')}")

            if poll_vote_form is not None:
                print(f"[DEBUG] poll_vote_form.is_valid() = {poll_vote_form.is_valid()}")
            else:
                print(f"[DEBUG] poll_vote_form is None after instantiation")

            if poll_vote_form and poll_vote_form.is_valid():
                selected_options_ids = poll_vote_form.cleaned_data['options']
                print(f"[DEBUG] Poll form valid. Selected options: {selected_options_ids}, type: {type(selected_options_ids)}")

                # BANDAGE FIX : Ensure selected_options_ids is always a list for uniform processing.
                # If it's a string (from PollVoteFormUnique/ChoiceField), wrap it in a list.
                # If it's already a list (from PollVoteFormMultiple/MultipleChoiceField), it remains unchanged.
                # This is to handle both single and multiple choice polls uniformly.
                # This is also a terrible hack, but it works for now.

                if not isinstance(selected_options_ids, list):
                    selected_options_ids = [selected_options_ids]
                    print(f"[DEBUG] Single choice poll detected, new type: {type(selected_options_ids)}")

                try:
                    # Clear previous votes by this user for this poll if poll doesn't allow multiple choices or user is changing vote
                    if poll.max_choices_per_user == 1:
                        for option in poll.options.all():
                            option.voters.remove(request.user)
                            print(f"[DEBUG] Removed user {request.user} from option {option.id}")

                    # Add new votes
                    for option_id in selected_options_ids:
                        try:
                            option = PollOption.objects.get(id=option_id, poll=poll)
                            print(f"[DEBUG] Found PollOption {option_id} for poll {poll.id}")
                            # Check if user can vote (not exceeding max_choices_per_user)
                            if poll.can_user_cast_new_vote(request.user) or option.voters.filter(id=request.user.id).exists():
                                 # If max_choices_per_user is 1, the previous votes are cleared, so this check might seem redundant
                                 # but it's good for >1 or unlimited, or if we want to allow changing a single vote.
                                option.voters.add(request.user)
                                print(f"[DEBUG] Added user {request.user} to option {option.id}")
                            else:
                                print(f"[DEBUG] User {request.user.username} cannot cast more votes for poll {poll.id}")
                        except PollOption.DoesNotExist as e:
                            print(f"[ERROR] PollOption.DoesNotExist: {e} (option_id={option_id}, poll={poll.id})")
                            # Handle error: option not found or doesn't belong to this poll
                            pass
                except Exception as e:
                    print(f"[ERROR] Exception during poll vote processing: {e}")
                base_url = request.get_full_path()
                redirect_url = f"{base_url}#top"
                return redirect(redirect_url) # Redirect to refresh and show results
            else:
                if poll_vote_form:
                    print(f"[ERROR] Poll form is NOT valid. Errors: {poll_vote_form.errors}")
        else:
            if poll.max_choices_per_user == 1:
                poll_vote_form = PollVoteFormUnique(poll_options=poll.options.all())
                print(f"[DEBUG] Instantiated PollVoteFormUnique for GET or non-vote POST")
            else:
                poll_vote_form = PollVoteFormMultiple(poll_options=poll.options.all())
                print(f"[DEBUG] Instantiated PollVoteFormMultiple for GET or non-vote POST")

    if request.method == 'POST':
        print(f"[DEBUG] Request POST : {request.POST}")
        if 'reply' in request.POST:
            form = QuickReplyForm(request.POST, user=request.user, topic=topic)
            sort_form = RecentPostsForm(request.GET or None)
            if form.is_valid():
                new_post = form.save()
                print(f"[DEBUG] QuickReplyForm valid, new post id: {new_post.id}")
                return redirect('post-redirect', new_post.id)
            else:
                print(f"[ERROR] QuickReplyForm errors: {form.errors}")
        elif 'sort' in request.POST:
            sort_form = RecentPostsForm(request.POST)
            form = QuickReplyForm(user=request.user, topic=topic)  # Initialize form here to prevent reference error
            if sort_form.is_valid():
                days = sort_form.cleaned_data['days']
                print(f"[DEBUG] Days : {days}")
                order = sort_form.cleaned_data['order']
                print(f"[DEBUG] Order : {order}")

                # Redirect to a URL with the parameters (e.g., same page)
                params = urlencode({'days': days, 'order': order})
                return redirect(f"{reverse('topic-details', args=[topicid, topicslug])}?{params}")
            else:
                print(f"[ERROR] RecentPostsForm errors: {sort_form.errors}")
        else:
            # Default case if neither 'reply' nor 'sort' is in request.POST
            form = QuickReplyForm(user=request.user, topic=topic)
            sort_form = RecentPostsForm(request.GET or None)
    else:
        form = QuickReplyForm(user=request.user, topic=topic)
        sort_form = RecentPostsForm(request.GET or None)

    if has_poll:
        user_can_vote_bool = user_can_vote(request.user, topic.poll)
        print(f"[DEBUG] user_can_vote_bool: {user_can_vote_bool}")

    render_quick_reply = True

    if request.user.is_authenticated == False or (topic.is_locked and not request.user.profile.is_user_staff):
        render_quick_reply = False
    else:
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_groups = user_profile.groups.all()
            # Check if the user has no group
            if user_groups.count() == 0:
                render_quick_reply = False
            else:
                # Check if the user is "Outsider" as top group
                top_group = user_profile.get_top_group
                if top_group.name == "Outsider":
                    render_quick_reply = False
        except Profile.DoesNotExist:
            render_quick_reply = False
    # print(f"LAST MESSAGE TIME : {topic.last_message_time}")

    # Get the neighboring topics
    try:
        previous_topic = Topic.objects.filter(last_message_time__lt=topic.last_message_time, parent=topic.parent, is_sub_forum=False).order_by('-last_message_time').first()
    except Topic.DoesNotExist as e:
        print(f"[ERROR] previous_topic Topic.DoesNotExist: {e}")
        previous_topic = None
    try:
        next_topic = Topic.objects.filter(last_message_time__gt=topic.last_message_time, parent=topic.parent, is_sub_forum=False).order_by('last_message_time').first()
    except Topic.DoesNotExist as e:
        print(f"[ERROR] next_topic Topic.DoesNotExist: {e}")
        next_topic = None

    smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

    context = {"posts": posts, 
               "tree":tree, 
               "topic":topic, 
               "subforum":subforum, 
               "form":form, 
               "pagination":pagination,
               "current_page" : current_page, 
               "max_page":max_page,
               "render_quick_reply":render_quick_reply, 
               "previous_topic":previous_topic, 
               "next_topic":next_topic, 
               "sort_form":sort_form,
               "smiley_categories":smiley_categories,
               "poll_vote_form":poll_vote_form,
               "user_can_vote":user_can_vote_bool,
               "has_poll":has_poll,
               "user_has_voted":user_has_voted,
               "poll_options": poll_options,
               }
    #print(f"[DEBUG] Rendering topic_details.html with context: posts={len(posts)}, topic={topic}, has_poll={has_poll}, poll_vote_form={poll_vote_form}, user_can_vote={user_can_vote_bool}")
    return theme_render(request, 'topic_details.html', context)

@ratelimit(key='user_or_ip', method=['POST'], rate='3/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/d')
def new_post(request):
    topic_id = request.GET.get('t')
    topic = Topic.objects.get(id=topic_id)
    if topic == None or topic.is_locked:
        if request.user.profile.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.", status=403)
        
    if topic.is_sub_forum:
        if request.user.profile.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.", status=403)

    tree = topic.get_tree

    if request.user.is_authenticated == False:
        return redirect("login-view")
    else:
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_groups = user_profile.groups.all()
            # Check if the user has no group
            if user_groups.count() == 0:
                return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.", status=403)
            else:
                # Check if the user is "Outsider" as top group
                top_group = user_profile.get_top_group
                if top_group.name == "Outsider":
                    return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.", status=403)
        except Profile.DoesNotExist:
            return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.", status=403)

    if request.method == 'POST':
        form = NewPostForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            new_post = form.save()
            return redirect('post-redirect', new_post.id)
    else:
        prefill = request.session.pop("prefill_message", "")
        form = NewPostForm(user=request.user, topic=topic)

    smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

    context = {
        'form': form,
        'topic': topic, 
        'tree': tree,
        'smiley_categories': smiley_categories,
    }

    return theme_render(request, 'new_post_form.html', context)

@ratelimit(key='user_or_ip', method=['GET'], rate='20/5s')
def category_details(request, categoryid, categoryslug): #TODO : [4] Add read status
    try:
        category = Category.objects.get(id=categoryid)
    except Category.DoesNotExist:
        return error_page(request, "Erreur", "La catégorie n'a pas été trouvée.", status=404)
    
    if request.method == 'POST':
        form = RecentTopicsForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            
            # Redirect to a URL with the parameters (e.g., same page)
            params = urlencode({'days': days})
            return redirect(f"{reverse('category-details', args=[categoryid, categoryslug])}?{params}")
    
    else:
        form = RecentTopicsForm(request.GET or None)

    days = int(request.GET.get('days', 0))

    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    index_topics = category.index_topics.select_related(
            'author', 'author__profile', 'author__profile__top_group', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__author__profile__top_group', 'poll',
            'latest_message__topic'
    ).all().order_by('id')
    
    root_not_index_topics = Topic.objects.annotate(
        is_root=Case(
            When(parent__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).select_related(
            'author', 'author__profile', 'author__profile__top_group', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__author__profile__top_group', 'poll'
    ).filter(is_root=True, category=category).exclude(id__in=index_topics.values_list('id', flat=True))


    if days > 0:
        # Filter topics based on the number of days
        date_threshold = timezone.now() - timezone.timedelta(days=days)
        index_topics = index_topics.filter(last_message_time__gte=date_threshold)
        root_not_index_topics = root_not_index_topics.filter(last_message_time__gte=date_threshold)

    announcements = utf.announcement_topics.select_related(
                'author', 'author__profile', 'author__profile__top_group', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'latest_message__author__profile__top_group', 'poll'
    ).all().order_by('-last_message_time')


    context = {
        "category": category,
        "index_topics": index_topics,
        "root_not_index_topics": root_not_index_topics,
        "forum": utf,
        "form": form,
        "announcements": announcements,
    }
    return theme_render(request, "category_details.html", context)


def search(request):
    return theme_render(request, "search.html")

@ratelimit(key='user_or_ip', method=['POST'], rate='5/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='50/d')
def edit_profile(request):
    if request.user.is_authenticated == False:
        return redirect("login-view")
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            for field in profile_form.changed_data:
                if field == "type":
                    if profile_form.cleaned_data.get(field) == '':
                        profile_form.instance.type = 'neutral' # Change to neutral if user chose "Sélectionner", also this is terrible but whatever
                        
            user_form.save()
            profile_form.save()

            edit_profile_url = reverse('edit-profile')
            profile_details_url = reverse('profile-details', args=[request.user.id])
            message = f"""
            Votre profil a été mis à jour avec succès.<br><br>
            <a href="{edit_profile_url}">Cliquez ici pour retourner sur votre profil</a><br><br>
            <a href="{profile_details_url}">Voir mon profil</a>
            """

            return error_page(request, "Informations", message, status=200)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    context = {'user_form': user_form, 'profile_form': profile_form}
    return theme_render(request, 'edit_profile.html', context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/30s')
def search_results(request):
    # TODO: [2] Optimize get_relative_id (get_relative_id is called for each post, which is inefficient)

    # Clean up the URL by removing default values
    cleaned_params = {}
    redirect_needed = False
    
    # Define default values
    defaults = {
        'order': 'ASC',
        'keyword': '',
        'search_terms': 'any',
        'author': '',
        'char_limit': '200',
        'in_subforum': '0',
        'in_category': '0',
        'search_time': '0',
        'search_fields': 'all',
        'sort_by': 'time',
        'show_results': 'posts',
        'search_id': '',
        'page': '1',
        'per_page': '15'
    }
    
    # Check each parameter and only keep non-default values
    for param, default_value in defaults.items():
        current_value = request.GET.get(param, default_value)
        if current_value != default_value:
            cleaned_params[param] = current_value
        elif param in request.GET:
            # Parameter exists but has default value, mark for redirect
            redirect_needed = True
    
    # If we need to redirect to clean URL
    if redirect_needed:
        if cleaned_params:
            return redirect(f"{reverse('search-results')}?{urlencode(cleaned_params)}")
        else:
            return redirect(reverse('search-results'))
    

    #Define custom filter and order by field
    custom_filter = Q()
    order_by_field = 'id'
    
    # Search query parameters
    order = request.GET.get('order', 'ASC')
    keyword = request.GET.get('keyword', '')
    search_terms = request.GET.get('search_terms', 'any')
    author = request.GET.get('author', '')
    char_limit = int(request.GET.get('char_limit', 200))
    in_subforum = int(request.GET.get('in_subforum', '0'))
    in_category = int(request.GET.get('in_category', '0'))
    search_time = int(request.GET.get('search_time', '0'))
    search_fields = request.GET.get('search_fields', 'all')
    sort_by = request.GET.get('sort_by', 'time')
    show_results = request.GET.get('show_results', 'posts')

    search_id = request.GET.get('search_id', '') # Special search
    if search_id != '':
        if search_id == "unanswered":
            # Find topics that have exactly 0 replies (only the initial post)
            # First, get all topics with their post counts
            post_counts = Post.objects.values('topic_id').annotate(post_count=Count('id'))
            
            # Filter for topics that have exactly 1 post (just the initial post)
            unanswered_topic_ids = [item['topic_id'] for item in post_counts if item['post_count'] == 1]
            
            # If we found any unanswered topics, filter the posts to only include those from these topics
            if unanswered_topic_ids:
                custom_filter &= Q(topic_id__in=unanswered_topic_ids)
            else:
                # If no unanswered topics found, use an impossible condition to return no results
                custom_filter &= Q(id__lt=0)

    if sort_by:
        if sort_by == "time":
            order_by_field = 'id'
        elif sort_by == "subject":
            order_by_field = 'topic__id'
        elif sort_by == "title":
            order_by_field = 'topic__title'
        elif sort_by == "author":
            order_by_field = 'author__username'
        elif sort_by == "forum":
            order_by_field = 'topic__parent__id'

        # Adjust for ascending/descending order

    if order == "DESC":
        if order_by_field.startswith('-'):
            order_by_field = order_by_field[1:]
        else:
            order_by_field = '-' + order_by_field

    if search_terms == "all":
        if keyword:
            if search_fields == "all":
                custom_filter &= Q(text__icontains=keyword) | Q(topic__title__icontains=keyword)
            elif search_fields == "msgonly":
                custom_filter &= Q(text__icontains=keyword)
    elif search_terms == "any":
        if keyword:
            keywords = keyword.split()
            keyword_filter = Q()
            for word in keywords:
                if search_fields == "all":
                    keyword_filter |= Q(text__icontains=word) | Q(topic__title__icontains=word)
                elif search_fields == "msgonly":
                    keyword_filter |= Q(text__icontains=word)
            custom_filter &= keyword_filter

    if author:
        custom_filter &= Q(author__username__iexact=author)

    if in_subforum != 0:
        try:
            subforum = Topic.objects.get(id=in_subforum)
            custom_filter &= Q(topic__parent=subforum)
        except Topic.DoesNotExist:
            return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche (Le sous-forum n'a pas été trouvé)", status=404)

    if in_category != 0:
        try:
            category = Category.objects.get(id=in_category)
            custom_filter &= Q(topic__category=category)
        except Category.DoesNotExist:
            return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche (La catégorie n'a pas été trouvé)", status=404)

    if search_time != 0:
        custom_filter &= Q(created_time__gte=timezone.now() - timezone.timedelta(days=search_time))

    # Pagination query parameters
    messages_per_page = min(int(request.GET.get('per_page', 15)),75)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * messages_per_page
    print(f"order by field : {order_by_field}")
    all_results = Post.objects.select_related('topic', 'author', 'topic__parent').filter(custom_filter).order_by(order_by_field)

    if show_results == "topics":
        # Get distinct topic IDs from the posts
        topic_ids = all_results.values_list('topic', flat=True).distinct()
        
        # Get the actual Topic objects using those IDs
        all_results = Topic.objects.select_related('parent', 'latest_message', 'latest_message__author', 'latest_message__author__profile', 'author', 'author__profile').filter(id__in=topic_ids)
        
        # Adjust ordering for Topic objects
        # Remove the 'topic__' prefix since we're querying Topic directly now
        topic_order_field = order_by_field.replace('topic__', '')
        all_results = all_results.order_by(topic_order_field)

    result_count = all_results.count()
    if result_count == 0:
        return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche", status=404)
    results = all_results[limit - messages_per_page : limit]

    max_page = (result_count + messages_per_page - 1) // messages_per_page
    pagination = generate_pagination(current_page, max_page)


    context =  {"results" : results, "result_count" : result_count, "char_limit":char_limit,
                "current_page" : current_page, "max_page" : max_page, "pagination" : pagination}
    if show_results == "topics":
        return theme_render(request, "search_results_topics.html", context)
    else:
        return theme_render(request, "search_results.html", context)

@csrf_exempt
def debug_csrf(request):
    """Debug view to check CSRF configuration."""
    return JsonResponse({
        'csrf_cookie': request.COOKIES.get('csrftoken', 'Not found'),
        'is_secure': request.is_secure(),
        'scheme': request.scheme,
        'headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
    })

@ratelimit(key='user_or_ip', method=['POST'], rate='3/10m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/d')
def edit_post(request, postid):
    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        return error_page(request, "Erreur", "Ce message n'existe pas.", status=404)
    
    topic = post.topic
    subforum = topic.parent

    if request.user.is_authenticated == False:
        return redirect("login-view")
    
    if post.author != request.user and request.user.profile.is_user_staff == False:
        return error_page(request, "Informations", "Vous ne pouvez pas modifier ce message.", status=403)
    
    if request.method == 'POST':
        form = NewPostForm(request.POST, instance=post, user=post.author, topic=topic) # oops this used to be request.user lol i'm dumb
        if form.is_valid():
            form.save()
            return redirect('post-redirect', post.id)
    else:
        form = NewPostForm(instance=post, user=request.user, topic=topic)

    smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

    context = {'form': form, 'topic': topic, "smiley_categories":smiley_categories}

    return theme_render(request, 'new_post_form.html', context)

@ratelimit(key='user_or_ip', method=['GET'], rate='5/5s')
def groups(request):
    #groups = ForumGroup.objects.all().
    if request.user.is_authenticated:
        user_groups = ForumGroup.objects.filter(users__user=request.user).distinct()
    else:
        user_groups = ForumGroup.objects.none()
    all_groups = ForumGroup.objects.prefetch_related('users').annotate(user_count=Count('users')).order_by('-priority')
    context = {"user_groups":user_groups, "all_groups":all_groups}
    return theme_render(request, "groups.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def groups_details(request, groupid):
    try:
        group = ForumGroup.objects.get(id=groupid)
    except ForumGroup.DoesNotExist:
        return error_page(request, "Erreur", "Ce groupe n'existe pas.", status=404)
    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page

    mods = User.objects.select_related('profile').filter(profile__groups__is_staff_group=True).distinct()
    # Get all members in the group (excluding mods)
    all_members = User.objects.select_related('profile').filter(profile__groups__id=groupid).exclude(id__in=mods.values_list('id', flat=True)).order_by('username')
    members = all_members[limit - members_per_page : limit]

    max_page  = (len(all_members) // members_per_page) + 1
    pagination = generate_pagination(current_page, max_page)

    context = {"group":group, "mods":mods, "members":members, "current_page" : current_page, "max_page":max_page, "pagination":pagination}
    return theme_render(request, "group_details.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def mark_as_read(request):
    if request.user.is_authenticated:
        subforum_param = request.GET.get('f', '')
        category_param = request.GET.get('c', '')
        dict = {
            'subforum': subforum_param,
            'category': category_param
        }
        func_output = mark_as_read_with_filter(request.user, dict)
        if func_output == False:
            return error_page(request, "Informations", "Aucun sujet ne correspond à vos critères de recherche.", status=404)
        elif func_output == True:
            return error_page(request, "Informations", "Tous les sujets ont été marqués comme lus.", status=200)
    else:
        return redirect("login-view")
    
def post_redirect(request, postid):
    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        return error_page(request, "Informations", "Ce message n'existe pas.", status=404)
    
    topic = post.topic
    
    posts_per_page = 15 # Maybe change this to a query parameter in the future, but for now it's fine
    page_redirect = get_post_page_in_topic(post.id, topic.id, posts_per_page)
    if page_redirect == None:
        page_redirect = 1
    if page_redirect == 1:
        return redirect(f"{reverse('topic-details', args=[topic.id, topic.slug])}#p{postid}")
    else:
        return redirect(f"{reverse('topic-details', args=[topic.id, topic.slug])}?page={page_redirect}#p{postid}")
    
@ratelimit(key='user_or_ip', method=['POST'], rate='20/m')
def post_preview(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        
        # Create a dummy post object with the current user's information
        dummy_post = {
            'author': request.user,
            'text': content,
            'created_time': timezone.now(),
        }
        
        context = {'post': dummy_post}

        return theme_render(request, 'post_preview.html', context)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def jumpbox_redirect(request):
    """
    Handles the jumpbox dropdown selections and redirects to the appropriate subforum or category
    """
    jump_target = request.GET.get('f', '-1')
    
    # If no selection or invalid selection
    if jump_target == '-1':
        return redirect('index')
    
    # Check if it's a category (format: "c123")
    if isinstance(jump_target, str) and jump_target.startswith('c'):
        try:
            category_id = int(jump_target[1:])
            category = Category.objects.get(id=category_id)
            return redirect('category-details', categoryid=category_id, categoryslug=category.slug)
        except (ValueError, Category.DoesNotExist):
            return redirect('index')
    
    # Otherwise, it's a subforum (format: "f123")
    try:
        print("Jumpbox redirect to subforum")
        subforum_id = int(jump_target[1:])
        print(f"Subforum ID: {subforum_id}")
        subforum = Topic.objects.get(id=subforum_id)
        print(f"Subforum: {subforum}")
        return redirect('subforum-details', subforumid=subforum_id, subforumslug=subforum.slug)
    except (ValueError, Topic.DoesNotExist):
        return redirect('index')
    
def prefill_new_post(request):
    if request.method == "POST":
        topic_id = request.GET.get("t")
        prefill_text = request.POST.get("prefill", "")
        request.session["prefill_message"] = prefill_text
        return redirect(f"{reverse('new-post')}?t=" + topic_id)
    else:
        return redirect("index")
    
def viewonline(request): 
    return theme_render(request, "viewonline.html")

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def removevotes(request, pollid):
    try:
        poll = Poll.objects.get(id=pollid)
    except Poll.DoesNotExist:
        return error_page(request, "Informations", "Ce sondage n'existe pas.", status=404)

    if poll is None:
        return error_page(request, "Informations", "Ce sondage n'existe pas.", status=404)
    
    if poll.is_active == False:
        return error_page(request, "Informations", "Ce sondage n'est plus actif.", status=403)
    
    if request.user.is_authenticated:
        if poll.can_change_vote == 1:
            # Remove all votes for the user in this poll
            for option in poll.options.all():
                if request.user in option.voters.all():
                    option.voters.remove(request.user)
                    print(f"[DEBUG] Removed user {request.user} from option {option.id}")
            return redirect('topic-details', topicid=poll.topic.id, topicslug=poll.topic.slug)
        else:
            return error_page(request, "Informations", "Vous n'avez pas le droit de supprimer vos votes sur ce sondage.")
    return redirect('login-view')

def pm_inbox(request):
    if request.user.is_authenticated == False:
        return redirect("login-view")
    folder = str(request.GET.get('folder', 'inbox')).lower()
    messages = None
    if folder == 'inbox':
        messages = PrivateMessage.objects.select_related('author', 'author__profile', 'recipient', 'recipient__profile', 'thread').prefetch_related('thread__messages').filter(recipient=request.user).order_by('-created_time')
    elif folder == 'sentbox':
        messages = PrivateMessage.objects.select_related('author', 'author__profile', 'recipient', 'recipient__profile', 'thread').prefetch_related('thread__messages').filter(author=request.user, is_read=True).order_by('-created_time')
    elif folder == 'outbox':
        messages = PrivateMessage.objects.select_related('author', 'author__profile', 'recipient', 'recipient__profile', 'thread').prefetch_related('thread__messages').filter(author=request.user, is_read=False).order_by('-created_time')
    context = {
        'messages': messages
    }
    return theme_render(request, "pm_inbox.html", context)

@ratelimit(key='user_or_ip', method=['POST'], rate='3/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/d')
def new_pm_thread(request):
    if request.user.is_authenticated == False:
        return redirect("login-view")
    smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')

    if request.method == 'POST':
        form = NewPMThreadForm(request.POST, user=request.user)
        if form.is_valid():
            new_thread = form.save()
            return redirect('pm-inbox')
    else:
        form = NewPMThreadForm(user=request.user)

    context = {
        'form': form,
        'smiley_categories': smiley_categories,
    }

    return theme_render(request, 'new_pm_thread_form.html', context)

def pm_details(request, messageid):
    if request.user.is_authenticated == False:
        return redirect("login-view")
    message = PrivateMessage.objects.select_related(
        'author', 'author__profile', 'recipient', 'recipient__profile', 'thread'
    ).prefetch_related('thread__messages'
    ).get(id=messageid)
    if message is None:
        return error_page(request, "Erreur", "Ce message n'existe pas.", status=404)
    if request.user != message.recipient and request.user != message.author and not request.user.profile.is_user_staff:
        return error_page(request, "Informations", "Vous n'avez pas le droit de voir ce message.", status=403)
    if request.user == message.recipient and not message.is_read:
        message.is_read = True
        message.save()
        print(f"[DEBUG] Marked message {messageid} as read")
    previous_messages = message.thread.messages.filter(created_time__lte=message.created_time).order_by('-created_time')
    print(f"[DEBUG] Previous messages count: {previous_messages.count()} for message {messageid}")
    context = {
        "message": message,
        "previous_messages": previous_messages,
    }
    return theme_render(request, "pm_details.html", context)

def new_pm(request, threadid):
    if request.user.is_authenticated == False:
        return redirect("login-view")
    
    try:
        thread = PrivateMessageThread.objects.get(id=threadid)
    except PrivateMessageThread.DoesNotExist:
        return error_page(request, "Erreur", "Ce fil de discussion n'existe pas.", status=404)
    
    if request.user != thread.author and request.user != thread.recipient and not request.user.profile.is_user_staff:
        return error_page(request, "Informations", "Vous n'avez pas le droit de répondre à ce fil de discussion.", status=403)

    if request.method == 'POST':
        form = NewPMForm(request.POST, user=request.user, thread=thread)
        if form.is_valid():
            new_message = form.save()
            return redirect('pm-details', messageid=new_message.id)
    else:
        form = NewPMForm(user=request.user, thread=thread)

    smiley_categories = SmileyCategory.objects.prefetch_related('smileys').order_by('id')
    context = {
        'form': form,
        'thread': thread,
        'smiley_categories': smiley_categories,
    }

    return theme_render(request, 'new_pm_form.html', context)

def choose_theme(request):
    """
    Render a form letting the user pick 'default' or 'modern'.
    Pre-select based on request.COOKIES['theme'] (default 'default').
    """
    current = request.COOKIES.get('theme', 'default')
    context = {'current_theme': current}
    return theme_render(request, 'choose_theme.html', context)

def set_theme(request):
    """
    Handle the POST from choose-theme.
    Sets the 'theme' cookie and redirects to `next`.
    """
    if request.method == 'POST':
        theme = request.POST.get('theme', 'default')
        next_url = request.POST.get('next', '/')
        response = redirect(next_url)
        # set a 30-day cookie (or omit max_age for a session cookie)
        response.set_cookie(
            'theme',
            theme,
            max_age=30*24*3600,
            httponly=False,
            samesite='Lax'
        )
        return response
    # fallback: go back to the chooser
    return redirect('choose-theme')