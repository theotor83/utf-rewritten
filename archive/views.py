# archive/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from forum.forms import UserRegisterForm, ProfileForm, NewTopicForm, NewPostForm, QuickReplyForm, MemberSortingForm, UserEditForm, RecentTopicsForm, RecentPostsForm, PollForm, PollVoteFormUnique, PollVoteFormMultiple
from .models import ArchiveProfile, ArchiveForumGroup, User, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, FakeUser
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Case, When, Value, BooleanField, Q, Count, F, Prefetch, Max, Subquery, OuterRef, IntegerField
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from precise_bbcode.models import SmileyTag
from django.utils.dateparse import parse_datetime
from django.core.cache import cache
from datetime import datetime, time
from django.utils.timezone import make_aware
from django.db import connections
from django.db.models.functions import Coalesce


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
    return False

def get_percentage(small, big):
    try:
        return abs(round((small / big) * 100.0, 2)) if big != 0 else 0.00
    except ZeroDivisionError:
        return 0.00

def get_descendants_map(subforum_ids):
    """
    Efficiently builds a map of subforums to all their descendant topics.
    This helps avoid recursive database queries in the view.
    """
    if not subforum_ids:
        return {}

    descendants_map = {sf_id: [] for sf_id in subforum_ids}
    
    # Get all topics that have a parent in the subforum list
    all_topics = ArchiveTopic.objects.all().select_related('parent')
    topic_dict = {topic.id: topic for topic in all_topics}
    
    parent_child_map = {}
    for topic in all_topics:
        if topic.parent_id:
            if topic.parent_id not in parent_child_map:
                parent_child_map[topic.parent_id] = []
            parent_child_map[topic.parent_id].append(topic)

    for sf_id in subforum_ids:
        queue = list(parent_child_map.get(sf_id, []))
        visited = set(t.id for t in queue)
        
        while queue:
            current_topic = queue.pop(0)
            descendants_map[sf_id].append(current_topic)
            
            # If the current topic is a subforum, add its children to the queue
            if current_topic.id in parent_child_map:
                for child in parent_child_map[current_topic.id]:
                    if child.id not in visited:
                        queue.append(child)
                        visited.add(child.id)
                        
    return descendants_map

def get_message_frequency(message_count, date_joined, date_now=None):
    if date_now is None:
        date_now = timezone.now()
    
    # # Ensure date_joined is timezone-aware
    # if date_joined.tzinfo is None:
    #     raise ValueError("date_joined must be timezone-aware")
    
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

def get_post_page_in_topic(post_id, topic_id, posts_per_page=50):
    try:
        post = ArchivePost.objects.get(id=post_id, topic_id=topic_id)
        topic = post.topic
        relative_position = topic.archive_replies.filter(created_time__lte=post.created_time).count()
        page_number = (relative_position // posts_per_page) + 1
        return page_number
    except ArchivePost.DoesNotExist:
        return None
    
def mark_all_topics_read_for_user(user):
    """Mark all topics as read for the user."""
    return

# TODO: [2] Make the filter recursive for nested subforums
def mark_as_read_with_filter(user, filter_dict):
    return

def user_can_vote(user, poll):
    """Check if the user can vote in the poll, assuming users can't change their votes."""
    return False


def views_get_total_messages(before_datetime=None):
    """A template tag to get the total number of messages in the forum, with support for past dates."""

    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"total_messages_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    past_total_messages = ArchivePost.objects.filter(created_time__lte=before_datetime if before_datetime else timezone.now()).count()

    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, past_total_messages, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {past_total_messages} messages")
    return past_total_messages

def views_get_user_message_count(user, before_datetime=None):
    """A template tag to get the total number of messages of a user, with support for past dates."""
    # Create cache key based on user ID and datetime
    datetime_str = before_datetime.strftime('%Y-%m-%d') if before_datetime else 'now'
    cache_key = f"user_message_count_{user.id}_{datetime_str}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        #print(f"Cache hit for {cache_key}")
        return cached_result
    
    # Perform the database query
    message_count = ArchivePost.objects.filter(author=user, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
    
    # Cache the result for 12 hours (60*60*12 seconds)
    cache.set(cache_key, message_count, 60*60*12)
    #print(f"Cache miss for {cache_key}, calculated {message_count} messages")
    return message_count

def get_past_user_group(user, before_datetime=None):
    user_group = user.archiveprofile.get_top_group
    if not user_group:
        result = None
    elif user_group.name == "Outsider" or user_group.priority > 75: # Every group with priority > 75 is a "special user" group, like staff or custom group.
        result = user_group
    else:
        # If the user is a "regular user", we need to calculate the user's message count before the given date, and return the group based on that.
        message_count = ArchivePost.objects.filter(author=user, created_time__lte=before_datetime if before_datetime else timezone.now()).count()
        # Now, get the group with the highest "minimum_messages" value that is less than or equal to the message count.
        group = ArchiveForumGroup.objects.filter(is_messages_group=True, minimum_messages__lte=message_count).first()
        #print(f"User {user.username} has {message_count} messages, group: {group.name if group else 'None'}")
        result = group if group else user_group
    return result

# Create your views here.

def index_redirect(request):
    return redirect("archive:index")

@ratelimit(key='user_or_ip', method=['GET'], rate='5/10s')
@ratelimit(key='user_or_ip', method=['GET'], rate='200/h')

@ratelimit(key='user_or_ip', method=['POST'], rate='3/5m')
def index(request):
    fake_datetime = timezone.now()  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str)  # can return None
    if not fake_datetime:
        fake_datetime = timezone.now()  # Fallback to current time if parsing fails

    
    if fake_datetime:
        # === Define all queries and subqueries first ===

        topic_table = ArchiveTopic._meta.db_table
        post_table = ArchivePost._meta.db_table

        # Raw query for sub-forum total reply COUNTS
        raw_query_replies = f"""
            WITH RECURSIVE topic_descendants AS (
                SELECT id AS root_id, id AS topic_id FROM {topic_table} WHERE is_sub_forum = TRUE
                UNION ALL
                SELECT td.root_id, t.id AS topic_id FROM {topic_table} AS t JOIN topic_descendants AS td ON t.parent_id = td.topic_id
            )
            SELECT td.root_id as topic_id, COUNT(p.id) AS total_replies
            FROM topic_descendants td JOIN {post_table} p ON td.topic_id = p.topic_id
            WHERE p.created_time <= %s GROUP BY td.root_id;
        """

        # Raw query for sub-forum latest post IDS
        raw_query_latest_post_ids = f"""
            WITH RECURSIVE topic_descendants AS (
                SELECT id AS root_id, id AS topic_id FROM {topic_table} WHERE is_sub_forum = TRUE
                UNION ALL
                SELECT td.root_id, t.id AS topic_id FROM {topic_table} AS t JOIN topic_descendants AS td ON t.parent_id = td.topic_id
            ),
            ranked_posts AS (
                SELECT td.root_id, p.id as post_id,
                ROW_NUMBER() OVER(PARTITION BY td.root_id ORDER BY p.created_time DESC, p.id DESC) as rn
                FROM topic_descendants td JOIN {post_table} p ON td.topic_id = p.topic_id
                WHERE p.created_time <= %s
            )
            SELECT root_id, post_id FROM ranked_posts WHERE rn = 1;
        """

        # Subquery for regular topic post COUNTS
        regular_topic_posts = Subquery(
            ArchivePost.objects.filter(topic=OuterRef('pk'), created_time__lte=fake_datetime)
            .values('topic').annotate(c=Count('id')).values('c'),
            output_field=IntegerField()
        )

        # Subquery for topic children COUNTS
        past_children_count = Subquery(
            ArchiveTopic.objects.filter(parent=OuterRef('pk'), created_time__lte=fake_datetime)
            .values('parent').annotate(c=Count('id')).values('c'),
            output_field=IntegerField()
        )

        # Subquery for regular topic latest post ID
        latest_regular_post_id = Subquery(
            ArchivePost.objects.filter(topic=OuterRef('pk'), created_time__lte=fake_datetime)
            .order_by('-created_time', '-id').values('pk')[:1],
            output_field=IntegerField()
        )

        # === Execute Raw Queries ===
        subforum_replies_map = {}
        subforum_latest_post_ids_map = {}
        with connections['archive'].cursor() as cursor:
            # Execute first raw query
            cursor.execute(raw_query_replies, [fake_datetime])
            for row in cursor.fetchall():
                subforum_replies_map[row[0]] = row[1]
            # Execute second raw query
            cursor.execute(raw_query_latest_post_ids, [fake_datetime])
            for row in cursor.fetchall():
                subforum_latest_post_ids_map[row[0]] = row[1]

        # === Build and Execute Main Topic QuerySet ===
        # This single queryset fetches all topics and annotates them with all necessary non-recursive data
        index_topics_qs = ArchiveTopic.objects.filter(
            is_index_topic=True, category__is_hidden=False
        ).annotate(
            past_total_posts=Coalesce(regular_topic_posts, 0),
            past_total_children=Coalesce(past_children_count, 0),
            latest_regular_post_id=latest_regular_post_id
        ).order_by('category_id', '-id')

        # === Collect All Post IDs for latest_message_relative ===
        all_post_ids_to_fetch = set(subforum_latest_post_ids_map.values())
        for topic in index_topics_qs:
            if topic.latest_regular_post_id:
                all_post_ids_to_fetch.add(topic.latest_regular_post_id)

        # === Fetch All Post Objects in One Query ===
        latest_posts_map = {
            post.id: post for post in ArchivePost.objects.filter(id__in=all_post_ids_to_fetch)
            .select_related('author__archiveprofile', 'topic')
        }

        # === Stitch Everything Together for the Template ===
        categories = list(ArchiveCategory.objects.filter(is_hidden=False).order_by('id'))
        categories_dict = {cat.id: cat for cat in categories}
        for cat in categories:
            cat.processed_topics = []

        for topic in index_topics_qs:
            # Attach past_total_replies
            if topic.is_sub_forum:
                topic.past_total_replies = subforum_replies_map.get(topic.id, 0)
            else:
                topic.past_total_replies = max(0, topic.past_total_posts - 1)

            # past_total_children is already attached by the annotation.

            # Attach latest_message_relative
            latest_post_id = subforum_latest_post_ids_map.get(topic.id) if topic.is_sub_forum else topic.latest_regular_post_id
            topic.latest_message_relative = latest_posts_map.get(latest_post_id)

            # Attach other flags
            topic.is_unread = False

            # Add the fully processed topic to the correct category list
            parent_category = categories_dict.get(topic.category_id)
            if parent_category:
                parent_category.processed_topics.append(topic)

    else:
        categories = ArchiveCategory.objects.filter(is_hidden=False).prefetch_related(last_post_prefetch)
    
        all_index_topics = []
        for category in categories:
            # Using list() to execute the query and cache results
            try:
                # Use the prefetched attribute if it exists
                category.processed_topics = category.prefetched_index_topics
            except AttributeError:
                # Fallback to a direct query if prefetch didn't work for some reason
                category.processed_topics = list(category.index_topics.all().order_by('-id'))
            
            all_index_topics.extend(category.processed_topics)

        # User never authenticated, so no read status
        for topic in all_index_topics:
            topic.is_unread = False

    if request.method == "POST":
        return HttpResponse(status=403)
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('archive:index')
    else:
        form = AuthenticationForm()
    utf, created = ArchiveForum.objects.get_or_create(name='UTF')
    if created:
        #print("Forum UTF created")
        utf.save()

    last_post_prefetch = Prefetch(
        'index_topics',
        queryset=ArchiveTopic.objects.select_related('latest_message__author', 'latest_message__author__archiveprofile', 'latest_message__topic').order_by('id'),
        to_attr='prefetched_index_topics'
    )


    #online = FakeUser.objects.filter(archiveprofile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30))

    groups = ArchiveForumGroup.objects.all()

    try:
        presentations = ArchiveTopic.objects.filter(is_sub_forum=True, title="Présentations").first()
    except ArchiveTopic.DoesNotExist:
        presentations = None
    try:
        regles = ArchiveTopic.objects.filter(is_sub_forum=False, is_announcement=True).first()
    except ArchiveTopic.DoesNotExist:
        regles = None

    if fake_datetime:
        today = fake_datetime.date()
    else:
        today = timezone.now().date()
    next_week = today + timezone.timedelta(days=7)

    birthdays_today = FakeUser.objects.select_related('archiveprofile').filter(
        archiveprofile__birthdate__day=today.day,
        archiveprofile__birthdate__month=today.month,
        date_joined__lte=fake_datetime
    )

    if today.month == next_week.month:
        birthdays_in_week = FakeUser.objects.select_related('archiveprofile').filter(
            archiveprofile__birthdate__month=today.month,
            archiveprofile__birthdate__day__gte=today.day,
            archiveprofile__birthdate__day__lte=next_week.day,
            date_joined__lte=fake_datetime
        )
    else:
        birthdays_in_week = FakeUser.objects.select_related('archiveprofile').filter(
            Q(archiveprofile__birthdate__month=today.month, archiveprofile__birthdate__day__gte=today.day, date_joined__lte=fake_datetime) |
            Q(archiveprofile__birthdate__month=next_week.month, archiveprofile__birthdate__day__lte=next_week.day, date_joined__lte=fake_datetime)
        )
    

    # Quick access
    recent_posts = ArchivePost.objects.select_related('topic', 'author').filter(topic__is_sub_forum=False, created_time__lte=fake_datetime).order_by('-created_time')[:6]

    recent_topic_with_poll = ArchiveTopic.objects.filter(archive_poll__isnull=False, created_time__lte=fake_datetime).order_by('-created_time').first()

    context = {
        "categories": categories,
        "utf":utf,
        #"online":online,
        "form": form,
        "groups":groups,
        "presentations":presentations,
        "regles":regles,
        "birthdays_today":birthdays_today,
        "birthdays_in_week":birthdays_in_week,
        "recent_posts": recent_posts,
        "recent_topic_with_poll": recent_topic_with_poll,
        "fake_datetime": fake_datetime,
    }

    return render(request, "archive/index.html", context)

def faq(request):
    return render(request, "archive/faq.html")

def register_regulation(request):
    return render(request, "archive/register_regulation.html")

@ratelimit(key='user_or_ip', method=['POST'], rate='3/h')
@ratelimit(key='user_or_ip', method=['POST'], rate='5/d')
def register(request):
    return render(request, 'archive/register.html')

def error_page(request, error_title, error_message):
    context = {"error_title":error_title, "error_message":error_message}
    return render(request, "archive/error_page.html", context)

@ratelimit(key='user_or_ip', method=['POST'], rate='10/5m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/12h')
def login_view(request):
    return render(request, "archive/login.html")

def logout_view(request):
    logout(request)
    return redirect("archive:index")

@ratelimit(key='user_or_ip', method=['GET'], rate='5/5s')
def profile_details(request, userid):
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

        # Parse as date object
        date_obj = datetime.strptime(datetime_str, "%Y-%m-%d").date()
        # Convert to datetime (midnight)
        naive_datetime = datetime.combine(date_obj, time.min)
        # Make it timezone-aware
        fake_datetime_obj = make_aware(naive_datetime)

    if fake_datetime:
        past_total_message = views_get_total_messages(fake_datetime)
        print(f"Total messages in archive at {fake_datetime}: {past_total_message}")
        try:
            requested_user = FakeUser.objects.get(id=userid, date_joined__lte=fake_datetime)
        except FakeUser.DoesNotExist:
            return error_page(request, "Informations", "Désolé, mais cet utilisateur n'existe pas.")
        past_messages_count = views_get_user_message_count(requested_user, fake_datetime)
        percentage = get_percentage(past_messages_count, past_total_message)
        message_frequency = get_message_frequency(past_messages_count, requested_user.date_joined, fake_datetime_obj)

    else:
        utf, created = ArchiveForum.objects.get_or_create(name='UTF')
        if created:
            utf.save()

        try :
            requested_user = FakeUser.objects.get(id=userid)
        except:
            return error_page(request, "Informations", "Désolé, mais cet utilisateur n'existe pas.")
        
        percentage = get_percentage(requested_user.archiveprofile.messages_count, utf.total_messages)
        message_frequency = get_message_frequency(requested_user.archiveprofile.messages_count, requested_user.date_joined)
        
    context = {"req_user" : requested_user, "percentage" : percentage, "message_frequency" : message_frequency, "fake_datetime": fake_datetime}
    return render(request, "archive/profile_page.html", context)
    
@ratelimit(key='user_or_ip', method=['GET'], rate='10/30s')
def member_list(request):
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page
    
    # Get all profile user IDs from the archive database
    if fake_datetime:
        all_members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__isnull=False, date_joined__lte=fake_datetime).order_by('-id')
    else:
        all_members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__isnull=False).order_by('-id')
    count = all_members.count()
    max_page = (count + members_per_page - 1) // members_per_page

    pagination = generate_pagination(current_page, max_page)

    if request.method == 'POST':
        form = MemberSortingForm(request.POST)
        if form.is_valid():
            mode = form.cleaned_data['mode']
            order = form.cleaned_data['order']

            date_value = request.GET.get("date")
            if date_value:
                # Same date value, redirect with parameters
                params = urlencode({'date': date_value,'mode': mode, 'order': order})
                return redirect(f"{reverse('archive:member-list')}?{params}")
            else:
                # Redirect to a URL with the parameters (e.g., same page)
                params = urlencode({'mode': mode, 'order': order})
                return redirect(f"{reverse('archive:member-list')}?{params}")
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
            order_by_field = "archiveprofile__last_login"
        elif mode == "username":
            order_by_field = "username"
        elif mode == "posts":
            if fake_datetime:
                # When fake_datetime is set, we need to calculate dynamic message counts for sorting
                # We'll handle the sorting after retrieving all users and calculating their counts
                order_by_field = "id"  # Use a basic field for now, we'll sort manually later
            else:
                order_by_field = "archiveprofile__messages_count"
        elif mode == "email":
            custom_filter = {"archiveprofile__email_is_public": True}
            order_by_field = "id"
        elif mode == "website":
            custom_filter = {"archiveprofile__website__isnull": False}
            order_by_field = "id"
        elif mode == "topten":
            # Get top 10 posters based on message count up to fake_datetime if specified
            if fake_datetime:
                # Get all users with their message counts up to fake_datetime
                users_with_counts = FakeUser.objects.select_related('archiveprofile').filter(
                    archiveprofile__isnull=False,
                    date_joined__lte=fake_datetime
                ).annotate(
                    fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime)),
                    fake_last_visit=Max('archive_posts__created_time', filter=Q(archive_posts__created_time__lte=fake_datetime))
                ).order_by('-fake_message_count')[:10]
                members = list(users_with_counts)
            else:
                # Always get top 10 posters regardless of pagination (original behavior)
                members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__isnull=False).order_by('-archiveprofile__messages_count')[:10]  # Descending order + limit 10
            # Disable pagination for top10 mode
            pagination = []

        # Apply ordering before slicing
        if order == "DESC":
            order_by_field = f"-{order_by_field}"  # Prefix with '-' for descending order
        
        if members is None:
            # Only apply pagination for non-topten modes
            if custom_filter is not None:
                if fake_datetime:
                    if mode == "posts":
                        # For posts sorting with fake_datetime, we need all users to calculate and sort properly
                        all_users = FakeUser.objects.select_related('archiveprofile').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime)), fake_last_visit=Max('archive_posts__created_time', filter=Q(archive_posts__created_time__lte=fake_datetime))).filter(archiveprofile__isnull=False, date_joined__lte=fake_datetime, **custom_filter)
                        members = list(all_users)  # Convert to list for custom sorting later
                    else:
                        members = FakeUser.objects.select_related('archiveprofile').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime)), fake_last_visit=Max('archive_posts__created_time', filter=Q(archive_posts__created_time__lte=fake_datetime))).filter(archiveprofile__isnull=False, date_joined__lte=fake_datetime, **custom_filter).order_by(order_by_field)[limit - members_per_page : limit]
                else:
                    members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__isnull=False, **custom_filter).order_by(order_by_field)[limit - members_per_page : limit]
            else:
                if fake_datetime:
                    if mode == "posts":
                        # For posts sorting with fake_datetime, we need all users to calculate and sort properly
                        all_users = FakeUser.objects.select_related('archiveprofile').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime)), fake_last_visit=Max('archive_posts__created_time', filter=Q(archive_posts__created_time__lte=fake_datetime))).filter(archiveprofile__isnull=False, date_joined__lte=fake_datetime)
                        members = list(all_users)  # Convert to list for custom sorting later
                    else:
                        members = FakeUser.objects.select_related('archiveprofile').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime)), fake_last_visit=Max('archive_posts__created_time', filter=Q(archive_posts__created_time__lte=fake_datetime))).filter(archiveprofile__isnull=False, date_joined__lte=fake_datetime).order_by(order_by_field)[limit - members_per_page : limit]
                else:
                    members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__isnull=False).order_by(order_by_field)[limit - members_per_page : limit]

    # When fake_datetime is set, calculate dynamic message counts and last visit dates
    if fake_datetime and members:
        for member in members:
            # Get the latest message date for this user before fake_datetime
            # Handle exception if the user never logged in (01/01/2000)
            if member.archiveprofile.last_login.year == 2000:
                member.fake_last_visit = member.archiveprofile.last_login
            else:
                datetimes = [
                    member.fake_last_visit if hasattr(member, 'fake_last_visit') else None,
                    member.date_joined
                ]

                # Remove None values
                valid_datetimes = [dt for dt in datetimes if dt is not None]
                latest = max(valid_datetimes)

                member.fake_last_visit = latest
        
        # If sorting with fake_datetime, sort by the calculated fake_message_count
        if mode == "posts":
            reverse_order = order == "DESC"
            members = sorted(members, key=lambda x: x.fake_message_count, reverse=reverse_order)
            # Apply pagination after sorting
            members = members[limit - members_per_page : limit]

        # If sorting with fake_datetime, sort by the calculated fake_last_visit
        elif mode == "lastvisit":
            reverse_order = order == "DESC"
            members = sorted(members, key=lambda x: x.fake_last_visit, reverse=reverse_order)
            # Apply pagination after sorting
            members = members[limit - members_per_page : limit]

    counter = current_page * members_per_page - members_per_page + 1

    context =  {"members" : members, "current_page" : current_page, "max_page":max_page, "pagination":pagination, "form":form, "counter":counter, "fake_datetime": fake_datetime}

    return render(request, "archive/memberlist.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='50/5s')
def subforum_details(request, subforum_display_id, subforumslug):
    try:
        subforum = ArchiveTopic.objects.get(display_id=subforum_display_id, slug=subforumslug, is_sub_forum=True)
    except ArchiveTopic.DoesNotExist:
        return error_page(request, "Erreur", "Ce sous-forum n'existe pas.")
    
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

    tree = subforum.get_tree

    if fake_datetime:
        # Get all direct children topics
        topics_qs = subforum.archive_children.filter(is_sub_forum=False, created_time__lte=fake_datetime).order_by('-is_pinned', '-last_message_time')

        # Get all direct children subforums
        all_subforums = subforum.archive_children.filter(is_sub_forum=True, created_time__lte=fake_datetime).order_by('id')

        # For each subforum, check if it has unread content
        for sf in all_subforums:
            sf.unread = check_subforum_unread(sf, request.user)

        # For each topic, check if it has unread content and poll
        topics_list = list(topics_qs)
        
        for topic in topics_list:
            topic.has_poll = hasattr(topic, 'archive_poll')

    else:
        # Get all direct children topics
        topics_qs = subforum.archive_children.select_related('author', 'author__archiveprofile', 'latest_message', 'latest_message__author', 'latest_message__author__archiveprofile', 'archive_poll').filter(is_sub_forum=False).order_by('-is_pinned', '-last_message_time')

        # Get all direct children subforums 
        all_subforums = subforum.archive_children.filter(is_sub_forum=True).order_by('id')

        # For each subforum, check if it has unread content
        for sf in all_subforums:
            sf.unread = check_subforum_unread(sf, request.user)

        # For each topic, check if it has unread content and poll
        topics_list = list(topics_qs)
        
        for topic in topics_list:
            topic.has_poll = hasattr(topic, 'archive_poll')


    # Pagination
    current_page = int(request.GET.get('page', 1))
    posts_per_page = 50
    limit = current_page * posts_per_page
    count = len(topics_list)
    max_page = (count + posts_per_page - 1) // posts_per_page
    if max_page == 0:
        max_page = 1
    topics = topics_list[limit - posts_per_page : limit]

    pagination = generate_pagination(current_page, max_page)

    # Get all announcements
    if fake_datetime:
        try:
            utf = ArchiveForum.objects.get(name='UTF')
            announcement_topics = utf.announcement_topics.filter(created_time__lte=fake_datetime)
        except ArchiveForum.DoesNotExist:
            announcement_topics = []
    else:
        try:
            utf = ArchiveForum.objects.get(name='UTF')
            announcement_topics = utf.announcement_topics.select_related('author', 'author__archiveprofile', 'latest_message', 'latest_message__author', 'latest_message__author__archiveprofile', 'archive_poll').all()
        except ArchiveForum.DoesNotExist:
            announcement_topics = []

    # Check for unread announcements
    # User never authenticated, so no read status

    context = {
        "announcement_topics": announcement_topics,
        "topics": topics,
        "subforum": subforum,
        "tree": tree,
        "all_subforums": all_subforums,
        "pagination": pagination,
        "current_page": current_page,
        "max_page": max_page,
        "fake_datetime": fake_datetime,
    }
    return render(request, 'archive/subforum_details.html', context)

def test_page(request):
    return render(request, 'archive/test_page.html')

@ratelimit(key='user_or_ip', method=['POST'], rate='3/3m')
@ratelimit(key='user_or_ip', method=['POST'], rate='50/d')
def new_topic(request):
    if 'f' in request.GET and not 'c' in request.GET:
        subforum_id = request.GET.get('f')
        subforum = ArchiveTopic.objects.get(id=subforum_id)
        if subforum == None or subforum.is_sub_forum == False:
            return error_page(request, "Erreur", "Une erreur est survenue lors de la création du sujet.")

        tree = subforum.get_tree

        return redirect("archive:login-view")


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
                    # Create and save the ArchivePoll instance
                    poll_instance = ArchivePoll.objects.create(
                        topic=new_topic_instance,
                        question=poll_form.cleaned_data['question'],
                        days_to_vote=poll_form.cleaned_data['days_to_vote'],
                        max_choices_per_user=poll_form.cleaned_data['multiple_choice'],
                        can_change_vote=poll_form.cleaned_data['can_change_vote'],
                    )
                    # Create ArchivePollOption instances
                    for option_text in poll_form.cleaned_data['options']:
                        ArchivePollOption.objects.create(poll=poll_instance, text=option_text)
                
                return redirect(topic_details, new_topic_instance.id, new_topic_instance.slug)

        else: # GET request
            form = NewTopicForm(user=request.user, subforum=subforum)
            poll_form = PollForm()

        smiley_categories = ArchiveSmileyCategory.objects.prefetch_related('smileys').order_by('id')

        context = {
            'form': form, 
            'subforum': subforum, 
            'tree':tree,
            'smiley_categories': smiley_categories,
            'poll_form': poll_form,
        }

    elif 'c' in request.GET and not 'f' in request.GET:
        category_id = request.GET.get('c')
        category = ArchiveCategory.objects.get(id=category_id)
        if category == None:
            return error_page(request, "Erreur", "Une erreur est survenue lors de la création du sujet.")

        tree = {}

        return redirect("archive:login-view")
    
        if request.method == 'POST':
            form = NewTopicForm(request.POST, user=request.user, subforum=category)
            if form.is_valid():
                new_topic = form.save()
                return redirect(topic_details, new_topic.id, new_topic.slug)
        else:
            form = NewTopicForm(user=request.user, subforum=category)

        smiley_categories = ArchiveSmileyCategory.objects.prefetch_related('smileys').order_by('id')

        context = {
            'form': form, 
            'subforum': category, 
            'tree':tree,
            'smiley_categories': smiley_categories,
        }

    return redirect("archive:login-view")
    #return render(request, 'archive/new_topic_form.html', context)

@ratelimit(key='user_or_ip', method=['POST'], rate='8/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='200/d')
def topic_details(request, topicid, topicslug):
    try:
        topic = ArchiveTopic.objects.select_related('archive_poll', 'author', 'author__archiveprofile').prefetch_related('archive_poll__archive_options').get(id=topicid)
    except ArchiveTopic.DoesNotExist as e:
        return error_page(request, "Erreur", "Ce sujet n'existe pas.")
    
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

    subforum = topic.parent

    posts_per_page = min(int(request.GET.get('per_page', 15)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * posts_per_page
    if fake_datetime:
        all_posts = ArchivePost.objects.select_related('author', 'author__archiveprofile', 'author__archiveprofile__top_group').filter(topic=topic, created_time__lte=fake_datetime)
        count = all_posts.count()
    else:
        all_posts = ArchivePost.objects.select_related('author', 'author__archiveprofile', 'author__archiveprofile__top_group').filter(topic=topic)
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
        #print(f"[DEBUG] No posts found for topic {topic.id}")
        return error_page(request, "Informations","Il n'y a pas de messages.")

    pagination = generate_pagination(current_page, max_page)

    tree = topic.get_tree
    # for i in tree:
    #     print(f" tree : {tree}")
    
    #if posts.count() <= 0:
    #    return error_page(request, "Erreur","Ce sujet n'a pas de messages.")
    has_poll = hasattr(topic, 'archive_poll')
    poll_vote_form = None
    user_can_vote_bool = False # Default to False to avoid errors if poll_vote_form is None
    user_has_voted = 0
    poll_options = None


    if has_poll:
        poll = topic.archive_poll
        #print(f"[DEBUG] Poll found for topic {topic.id}: {poll}")

        poll_options = ArchivePollOption.objects.prefetch_related('voters').filter(poll=topic.archive_poll).order_by('id')
        # Get the total vote count for the poll once (We can use the poll's related manager for this.)
        total_poll_votes = poll.archive_options.aggregate(
            total=Count('voters')
        )['total'] or 0
        # Annotate each option with its vote count (only one query)
        poll_options = poll.archive_options.annotate(
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
    
        if request.method == 'POST' and 'submit_vote_button' in request.POST:
            return HttpResponse(status=403)
            #print(f"[DEBUG] Poll vote POST detected. Request POST data: {request.POST}")
            if request.POST.get('vote') == '1':
                # Determine which form class to use
                if topic.archive_poll.allow_multiple_choices:
                    CurrentPollVoteForm = PollVoteFormMultiple
                    #print("[DEBUG] Using PollVoteFormMultiple") # Debug print
                else:
                    CurrentPollVoteForm = PollVoteFormUnique
                    #print("[DEBUG] Using PollVoteFormUnique") # Debug print

                poll_vote_form = CurrentPollVoteForm(request.POST, poll_options=topic.archive_poll.archive_options.all())
                #print(f"[DEBUG] PollVoteForm instantiated: {poll_vote_form}")
            else:
                #print(f"[DEBUG] 'vote' not '1' in POST: {request.POST.get('vote')}")
                pass

            if poll_vote_form is not None:
                #print(f"[DEBUG] poll_vote_form.is_valid() = {poll_vote_form.is_valid()}")
                pass
            else:
                #print(f"[DEBUG] poll_vote_form is None after instantiation")
                pass

            if poll_vote_form and poll_vote_form.is_valid():
                selected_options_ids = poll_vote_form.cleaned_data['options']
                #print(f"[DEBUG] Poll form valid. Selected options: {selected_options_ids}, type: {type(selected_options_ids)}")

                # BANDAGE FIX : Ensure selected_options_ids is always a list for uniform processing.
                # If it's a string (from PollVoteFormUnique/ChoiceField), wrap it in a list.
                # If it's already a list (from PollVoteFormMultiple/MultipleChoiceField), it remains unchanged.
                # This is to handle both single and multiple choice polls uniformly.
                # This is also a terrible hack, but it works for now.

                if not isinstance(selected_options_ids, list):
                    selected_options_ids = [selected_options_ids]
                    #print(f"[DEBUG] Single choice poll detected, new type: {type(selected_options_ids)}")

                try:
                    # Clear previous votes by this user for this poll if poll doesn't allow multiple choices or user is changing vote
                    if poll.max_choices_per_user == 1:
                        for option in poll.archive_options.all():
                            option.voters.remove(request.user)
                            #print(f"[DEBUG] Removed user {request.user} from option {option.id}")

                    # Add new votes
                    for option_id in selected_options_ids:
                        try:
                            option = ArchivePollOption.objects.get(id=option_id, poll=poll)
                            #print(f"[DEBUG] Found ArchivePollOption {option_id} for poll {poll.id}")
                            # Check if user can vote (not exceeding max_choices_per_user)
                            if poll.can_user_cast_new_vote(request.user) or option.voters.filter(id=request.user.id).exists():
                                 # If max_choices_per_user is 1, the previous votes are cleared, so this check might seem redundant
                                 # but it's good for >1 or unlimited, or if we want to allow changing a single vote.
                                option.voters.add(request.user)
                                #print(f"[DEBUG] Added user {request.user} to option {option.id}")
                            else:
                                #print(f"[DEBUG] User {request.user.username} cannot cast more votes for poll {poll.id}")
                                pass
                        except ArchivePollOption.DoesNotExist as e:
                            #print(f"[ERROR] ArchivePollOption.DoesNotExist: {e} (option_id={option_id}, poll={poll.id})")
                            # Handle error: option not found or doesn't belong to this poll
                            pass
                except Exception as e:
                    #print(f"[ERROR] Exception during poll vote processing: {e}")
                    pass
                base_url = request.get_full_path()
                redirect_url = f"{base_url}#top"
                return redirect(redirect_url) # Redirect to refresh and show results
            else:
                if poll_vote_form:
                    #print(f"[ERROR] Poll form is NOT valid. Errors: {poll_vote_form.errors}")
                    pass
        else:
            if poll.max_choices_per_user == 1:
                poll_vote_form = PollVoteFormUnique(poll_options=poll.archive_options.all())
                #print(f"[DEBUG] Instantiated PollVoteFormUnique for GET or non-vote POST")
            else:
                poll_vote_form = PollVoteFormMultiple(poll_options=poll.archive_options.all())
                #print(f"[DEBUG] Instantiated PollVoteFormMultiple for GET or non-vote POST")

    if request.method == 'POST':
        #print(f"[DEBUG] Request POST : {request.POST}")
        if 'reply' in request.POST:
            return HttpResponse(status=403)
            form = QuickReplyForm(request.POST, user=request.user, topic=topic)
            sort_form = RecentPostsForm(request.GET or None)
            if form.is_valid():
                new_post = form.save()
                #print(f"[DEBUG] QuickReplyForm valid, new post id: {new_post.id}")
                return redirect('archive:post-redirect', new_post.id)
            else:
                #print(f"[ERROR] QuickReplyForm errors: {form.errors}")
                pass
        elif 'sort' in request.POST:
            sort_form = RecentPostsForm(request.POST)
            form = QuickReplyForm(user=request.user, topic=topic)  # Initialize form here to prevent reference error
            if sort_form.is_valid():
                days = sort_form.cleaned_data['days']
                #print(f"[DEBUG] Days : {days}")
                order = sort_form.cleaned_data['order']
                #print(f"[DEBUG] Order : {order}")

                # Redirect to a URL with the parameters (e.g., same page)
                params = urlencode({'days': days, 'order': order})
                return redirect(f"{reverse('archive:topic-details', args=[topicid, topicslug])}?{params}")
            else:
                #print(f"[ERROR] RecentPostsForm errors: {sort_form.errors}")
                pass
        else:
            # Default case if neither 'reply' nor 'sort' is in request.POST
            form = QuickReplyForm(user=request.user, topic=topic)
            sort_form = RecentPostsForm(request.GET or None)
    else:
        form = QuickReplyForm(user=request.user, topic=topic)
        sort_form = RecentPostsForm(request.GET or None)

    if has_poll:
        user_can_vote_bool = False
        #print(f"[DEBUG] user_can_vote_bool: {user_can_vote_bool}")

    render_quick_reply = False

    # if request.user.is_axuxtxhxexnxtxixcxaxtxexd == False or (topic.is_locked and not request.user.archiveprofile.is_user_staff):
    #     render_quick_reply = False
    # else:
    #     try:
    #         user_profile = ArchiveProfile.objects.get(user=request.user)
    #         user_groups = user_profile.groups.all()
    #         # Check if the user has no group
    #         if user_groups.count() == 0:
    #             render_quick_reply = False
    #         else:
    #             # Check if the user is "Outsider" as top group
    #             top_group = user_profile.get_top_group
    #             if top_group.name == "Outsider":
    #                 render_quick_reply = False
    #     except ArchiveProfile.DoesNotExist:
    #         render_quick_reply = False
    # print(f"LAST MESSAGE TIME : {topic.last_message_time}")

    # Get the neighboring topics
    if fake_datetime:
        try:
            previous_topic = ArchiveTopic.objects.filter(last_message_time__lt=topic.last_message_time, parent=topic.parent, is_sub_forum=False, created_time__lte=fake_datetime).order_by('-last_message_time').first()
        except ArchiveTopic.DoesNotExist as e:
            #print(f"[ERROR] previous_topic ArchiveTopic.DoesNotExist: {e}")
            previous_topic = None
        try:
            next_topic = ArchiveTopic.objects.filter(last_message_time__gt=topic.last_message_time, parent=topic.parent, is_sub_forum=False, created_time__lte=fake_datetime).order_by('last_message_time').first()
        except ArchiveTopic.DoesNotExist as e:
            #print(f"[ERROR] next_topic ArchiveTopic.DoesNotExist: {e}")
            next_topic = None
    else:
        try:
            previous_topic = ArchiveTopic.objects.filter(last_message_time__lt=topic.last_message_time, parent=topic.parent, is_sub_forum=False).order_by('-last_message_time').first()
        except ArchiveTopic.DoesNotExist as e:
            #print(f"[ERROR] previous_topic ArchiveTopic.DoesNotExist: {e}")
            previous_topic = None
        try:
            next_topic = ArchiveTopic.objects.filter(last_message_time__gt=topic.last_message_time, parent=topic.parent, is_sub_forum=False).order_by('last_message_time').first()
        except ArchiveTopic.DoesNotExist as e:
            #print(f"[ERROR] next_topic ArchiveTopic.DoesNotExist: {e}")
            next_topic = None

    smiley_categories = ArchiveSmileyCategory.objects.prefetch_related('smileys').order_by('id')

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
               "fake_datetime": fake_datetime,
               "poll_options": poll_options,
               }
    #print(f"[DEBUG] Rendering topic_details.html with context: posts={len(posts)}, topic={topic}, has_poll={has_poll}, poll_vote_form={poll_vote_form}, user_can_vote={user_can_vote_bool}")
    return render(request, 'archive/topic_details.html', context)

@ratelimit(key='user_or_ip', method=['POST'], rate='3/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='100/d')
def new_post(request):
    return redirect("archive:login-view") # User never authenticated, so redirect to login
    topic_id = request.GET.get('t')
    topic = ArchiveTopic.objects.get(id=topic_id)
    if topic == None or topic.is_locked:
        if request.user.archiveprofile.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.")
        
    if topic.is_sub_forum:
        if request.user.archiveprofile.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.")

    tree = topic.get_tree


    if request.method == 'POST':
        form = NewPostForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            new_post = form.save()
            return redirect('archive:post-redirect', new_post.id)
    else:
        prefill = request.session.pop("prefill_message", "")
        form = NewPostForm(user=request.user, topic=topic)

    smiley_categories = ArchiveSmileyCategory.objects.prefetch_related('smileys').order_by('id')

    context = {
        'form': form,
        'topic': topic, 
        'tree': tree,
        'smiley_categories': smiley_categories,
    }
    
    return render(request, 'archive/new_post_form.html', context)

@ratelimit(key='user_or_ip', method=['GET'], rate='20/5s')
def category_details(request, categoryid, categoryslug): #TODO : [4] Add read status
    try:
        category = ArchiveCategory.objects.get(id=categoryid)
    except ArchiveCategory.DoesNotExist:
        return error_page(request, "Erreur", "Category not found")
    
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None
    
    if request.method == 'POST':
        form = RecentTopicsForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            
            # Redirect to a URL with the parameters (e.g., same page)
            params = urlencode({'days': days})
            return redirect(f"{reverse('archive:category-details', args=[categoryid, categoryslug])}?{params}")
    
    else:
        form = RecentTopicsForm(request.GET or None)

    days = int(request.GET.get('days', 0))

    utf, created = ArchiveForum.objects.get_or_create(name='UTF')
    if created:
        #print("Forum UTF created")
        utf.save()
    
    if fake_datetime:
        index_topics = category.index_topics.filter(created_time__lte=fake_datetime).order_by('id')
        
        root_not_index_topics = ArchiveTopic.objects.annotate(
            is_root=Case(
                When(parent__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(is_root=True, category=category, created_time__lte=fake_datetime).exclude(id__in=index_topics.values_list('id', flat=True))


        if days > 0:
            # Filter topics based on the number of days
            date_threshold = timezone.now() - timezone.timedelta(days=days)
            index_topics = index_topics.filter(last_message_time__gte=date_threshold)
            root_not_index_topics = root_not_index_topics.filter(last_message_time__gte=date_threshold)

        announcements = utf.announcement_topics.filter(created_time__lte=fake_datetime).order_by('-last_message_time')
    
    else:

        index_topics = category.index_topics.all().order_by('id')
        
        root_not_index_topics = ArchiveTopic.objects.annotate(
            is_root=Case(
                When(parent__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(is_root=True, category=category).exclude(id__in=index_topics.values_list('id', flat=True))


        if days > 0:
            # Filter topics based on the number of days
            date_threshold = timezone.now() - timezone.timedelta(days=days)
            index_topics = index_topics.filter(last_message_time__gte=date_threshold)
            root_not_index_topics = root_not_index_topics.filter(last_message_time__gte=date_threshold)

        announcements = utf.announcement_topics.all().order_by('-last_message_time')

    context = {
        "category": category,
        "index_topics": index_topics,
        "root_not_index_topics": root_not_index_topics,
        "forum": utf,
        "form": form,
        "fake_datetime": fake_datetime,
        "announcements": announcements,
    }
    return render(request, "archive/category_details.html", context)
    
    
def search(request):
    return render(request, "archive/search.html")


@ratelimit(key='user_or_ip', method=['POST'], rate='5/m')
@ratelimit(key='user_or_ip', method=['POST'], rate='50/d')
def edit_profile(request):
    return redirect("archive:login-view") # User never authenticated, so redirect to login
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.archiveprofile)
        if user_form.is_valid() and profile_form.is_valid():
            for field in profile_form.changed_data:
                if field == "type":
                    if profile_form.cleaned_data.get(field) == '':
                        profile_form.instance.type = 'neutral' # Change to neutral if user chose "Sélectionner", also this is terrible but whatever
                        
            user_form.save()
            profile_form.save()

            edit_profile_url = reverse('archive:edit-profile')
            profile_details_url = reverse('archive:profile-details', args=[request.user.id])
            message = f"""
            Votre profil a été mis à jour avec succès.<br><br>
            <a href="{edit_profile_url}">Cliquez ici pour retourner sur votre profil</a><br><br>
            <a href="{profile_details_url}">Voir mon profil</a>
            """

            return error_page(request, "Informations", message)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.archiveprofile)

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'archive/edit_profile.html', context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/30s')
def search_results(request):
    # TODO: [2] Optimize get_relative_id (get_relative_id is called for each post, which is inefficient)
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
    sort_by = request.GET.get('sort_by', 'id')
    show_results = request.GET.get('show_results', 'posts')

    search_id = request.GET.get('search_id', '') # Special search
    if search_id != '':
        if search_id == "unanswered":
            # Find topics that have exactly 0 replies (only the initial post)
            # First, get all topics with their post counts
            post_counts = ArchivePost.objects.values('topic_id').annotate(post_count=Count('id'))
            
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
            # Sorting by author username across DBs is complex.
            # We will sort by author ID instead.
            order_by_field = 'author_id'
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
            subforum = ArchiveTopic.objects.get(id=in_subforum)
            custom_filter &= Q(topic__parent=subforum)
        except ArchiveTopic.DoesNotExist:
            return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche (Le sous-forum n'existe pas)")

    if in_category != 0:
        try:
            category = ArchiveCategory.objects.get(id=in_category)
            custom_filter &= Q(topic__category=category)
        except ArchiveCategory.DoesNotExist:
            return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche (La catégorie n'existe pas)")

    if search_time != 0:
        custom_filter &= Q(created_time__gte=timezone.now() - timezone.timedelta(days=search_time))

    # Pagination query parameters
    messages_per_page = min(int(request.GET.get('per_page', 15)),75)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * messages_per_page
    #print(f"order by field : {order_by_field}")
    all_results = ArchivePost.objects.select_related('topic', 'author', 'topic__parent').filter(custom_filter).order_by(order_by_field)

    if show_results == "topics":
        # Get distinct topic IDs from the posts
        topic_ids = all_results.values_list('topic', flat=True).distinct()
        
        # Get the actual ArchiveTopic objects using those IDs
        all_results = ArchiveTopic.objects.select_related('parent', 'latest_message', 'latest_message__author', 'latest_message__author__archiveprofile', 'author', 'author__archiveprofile').filter(id__in=topic_ids)
        
        # Adjust ordering for ArchiveTopic objects
        # Remove the 'topic__' prefix since we're querying ArchiveTopic directly now
        topic_order_field = order_by_field.replace('topic__', '')
        all_results = all_results.order_by(topic_order_field)

    result_count = all_results.count()
    if result_count == 0:
        return error_page(request, "Informations", "Aucun sujet ou message ne correspond à vos critères de recherche")
    results = all_results[limit - messages_per_page : limit]

    max_page = (result_count + messages_per_page - 1) // messages_per_page
    pagination = generate_pagination(current_page, max_page)


    context =  {"results" : results, "result_count" : result_count, "char_limit":char_limit,
                "current_page" : current_page, "max_page" : max_page, "pagination" : pagination}
    if show_results == "topics":
        return render(request, "archive/search_results_topics.html", context)
    else:
        return render(request, "archive/search_results.html", context)

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
    return redirect("archive:login-view") # User never authenticated, so redirect to login
    try:
        post = ArchivePost.objects.get(id=postid)
    except ArchivePost.DoesNotExist:
        return error_page(request, "Erreur", "Ce message n'existe pas.")
    
    topic = post.topic
    subforum = topic.parent
        
    
    if post.author != request.user and request.user.archiveprofile.is_user_staff == False:
        return error_page(request, "Informations", "Vous ne pouvez pas modifier ce message.")
    
    if request.method == 'POST':
        form = NewPostForm(request.POST, instance=post, user=post.author, topic=topic) # oops this used to be request.user lol i'm dumb
        if form.is_valid():
            form.save()
            return redirect('archive:post-redirect', post.id)
    else:
        form = NewPostForm(instance=post, user=request.user, topic=topic)

    smiley_categories = ArchiveSmileyCategory.objects.prefetch_related('smileys').order_by('id')

    return render(request, 'archive/new_post_form.html', {'form': form, 'topic': topic, "smiley_categories":smiley_categories})

@ratelimit(key='user_or_ip', method=['GET'], rate='5/5s')
def groups(request):
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

    user_groups = ArchiveForumGroup.objects.none()
    if fake_datetime:
        all_groups = ArchiveForumGroup.objects.prefetch_related('archive_users').all().order_by('-priority')
    else:
        all_groups = ArchiveForumGroup.objects.prefetch_related('archive_users').annotate(user_count=Count('archive_users')).order_by('-priority')
        
    if fake_datetime:
        for group in all_groups: # TODO: [1] Annotate it in the "all_groups" queryset instead of iterating. Still, the performance impact is negligible, as there are only 12 groups in the archive.
            if group.is_messages_group:
                if group.minimum_messages == 0:
                    group.user_count = FakeUser.objects.filter(date_joined__lte=fake_datetime).count() # This is more efficient, because the query is 100x faster than the one below (0.5ms vs 50ms)
                else:
                    potential_members = FakeUser.objects.prefetch_related('archive_posts').annotate(post_count_before=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime))).filter(post_count_before__gte=group.minimum_messages, date_joined__lte=fake_datetime)
                    group.user_count = potential_members.count()
            else:
                group.user_count = ArchiveProfile.objects.prefetch_related('user').filter(groups=group, user__date_joined__lte=fake_datetime).count()
    context = {"user_groups":user_groups, "all_groups":all_groups}
    return render(request, "archive/groups.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def groups_details(request, groupid):
    fake_datetime = None  # Initialize fake_datetime to None to avoid reference errors

    datetime_str = request.GET.get('date')  # structure : "2025-07-20"
    if datetime_str:
        fake_datetime = parse_datetime(datetime_str).date() # can return None

    try:
        group = ArchiveForumGroup.objects.get(id=groupid)
    except ArchiveForumGroup.DoesNotExist:
        return error_page(request, "Erreur", "Ce groupe n'existe pas.")
    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page

    if fake_datetime:
        mods = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__groups__is_staff_group=True, date_joined__lte=fake_datetime).distinct()
        # Get all members in the group (excluding mods)
        if group.is_messages_group:
            if group.minimum_messages == 5:
                # If the group has no minimum messages, we can just get all users who joined before the fake_datetime, to account for everyone with a -1 messages_count, meaning they are inactive.
                potential_members = FakeUser.objects.select_related('archiveprofile').prefetch_related('archive_posts').filter(date_joined__lte=fake_datetime).exclude(id__in=mods.values_list('id', flat=True)).order_by('username').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime))).annotate(fake_last_visit=Max('archive_posts__created_time'))
            else:
                # TODO: [0] Make this query ignore users whose top group's priority is lower than the group being queried, but this literally only applies to one user who has the "Outsider" group as top group for a joke (Kowai).
                potential_members = FakeUser.objects.select_related('archiveprofile').prefetch_related('archive_posts').filter(archiveprofile__messages_count__gte=group.minimum_messages, date_joined__lte=fake_datetime).exclude(id__in=mods.values_list('id', flat=True)).order_by('username').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime))).annotate(fake_last_visit=Max('archive_posts__created_time'))
            all_members = potential_members.filter(fake_message_count__gte=group.minimum_messages)
            members = all_members[limit - members_per_page : limit]
        else: # Staff group or other groups
            members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__groups__id=groupid, date_joined__lte=fake_datetime).exclude(id__in=mods.values_list('id', flat=True)).order_by('username').annotate(fake_message_count=Count('archive_posts', filter=Q(archive_posts__created_time__lte=fake_datetime))).annotate(fake_last_visit=Max('archive_posts__created_time'))[limit - members_per_page : limit]
        # When fake_datetime is set, calculate dynamic message counts and last visit dates
        if members:
            for member in members:
                if not hasattr(member, 'fake_last_visit'):
                    member.fake_last_visit = member.date_joined
                # Get the latest message date for this user before fake_datetime
                # Handle exception if the user never logged in (01/01/2000)
                if member.archiveprofile.last_login.year == 2000:
                    member.fake_last_visit = member.archiveprofile.last_login
                else:
                    datetimes = [
                        member.fake_last_visit,
                        member.archiveprofile.last_login,
                        member.date_joined
                    ]
                    # Remove None values
                    valid_datetimes = [dt for dt in datetimes if dt is not None]
                    latest = max(valid_datetimes)
                    member.fake_last_visit = latest
        if mods:
            for mod in mods:
                mod.fake_message_count = mod.archive_posts.filter(created_time__lte=fake_datetime).count()
                if mod.archiveprofile.last_login.year == 2000:
                    mod.fake_last_visit = mod.archiveprofile.last_login
                else:
                    latest_post = mod.archive_posts.filter(created_time__lte=fake_datetime).aggregate(
                        latest_date=Max('created_time')
                    )
                    datetimes = [
                        latest_post.get('latest_date'),
                        mod.archiveprofile.last_login,
                        mod.date_joined
                    ]
                    valid_datetimes = [dt for dt in datetimes if dt is not None]
                    latest = max(valid_datetimes)
                    mod.fake_last_visit = latest
    else:
        mods = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__groups__is_staff_group=True).distinct()
        # Get all members in the group (excluding mods)
        all_members = FakeUser.objects.select_related('archiveprofile').filter(archiveprofile__groups__id=groupid).exclude(id__in=mods.values_list('id', flat=True)).order_by('username')
        members = all_members[limit - members_per_page : limit]

    max_page  = (len(all_members) // members_per_page) + 1

    pagination = generate_pagination(current_page, max_page)

    context = {"group":group, "mods":mods, "members":members, "current_page" : current_page, "max_page":max_page, "pagination":pagination, "fake_datetime":fake_datetime}
    return render(request, "archive/group_details.html", context)

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def mark_as_read(request):
    return redirect("archive:login-view")
    
def post_redirect(request, postid):
    try:
        post = ArchivePost.objects.get(id=postid)
    except ArchivePost.DoesNotExist:
        return error_page(request, "Informations", "Ce message n'existe pas.")
    
    topic = post.topic
    
    posts_per_page = 15 # Maybe change this to a query parameter in the future, but for now it's fine
    page_redirect = get_post_page_in_topic(post.id, topic.id, posts_per_page)
    if page_redirect == None:
        page_redirect = 1
    if page_redirect == 1:
        return redirect(f"{reverse('archive:topic-details', args=[topic.id, topic.slug])}#p{postid}")
    else:
        return redirect(f"{reverse('archive:topic-details', args=[topic.id, topic.slug])}?page={page_redirect}#p{postid}")
    
@csrf_exempt
#@ratelimit(key='user_or_ip', method=['POST'], rate='20/m')
def post_preview(request):
    return HttpResponse(status=403)
    if request.method == 'POST':
        content = request.POST.get('content', '')
        author_instance = FakeUser.objects.get(id=3)
        
        # Create a dummy post object with the current user's information
        dummy_post = {
            'author': author_instance,
            'text': content,
            'created_time': timezone.now(),
        }
        
        context = {'post': dummy_post}
        
        return render(request, 'archive/post_preview.html', context)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def jumpbox_redirect(request):
    """
    Handles the jumpbox dropdown selections and redirects to the appropriate subforum or category
    """
    jump_target = request.GET.get('f', '-1')
    
    # If no selection or invalid selection
    if jump_target == '-1':
        return redirect('archive:index')
    
    # Check if it's a category (format: "c123")
    if isinstance(jump_target, str) and jump_target.startswith('c'):
        try:
            category_id = int(jump_target[1:])
            category = ArchiveCategory.objects.get(id=category_id)
            return redirect('archive:category-details', categoryid=category_id, categoryslug=category.slug)
        except (ValueError, ArchiveCategory.DoesNotExist):
            return redirect('archive:index')
    
    # Otherwise, it's a subforum (format: "f123")
    try:
        #print("Jumpbox redirect to subforum")
        subforum_id = int(jump_target[1:])
        #print(f"Subforum ID: {subforum_id}")
        subforum = ArchiveTopic.objects.get(id=subforum_id)
        #print(f"Subforum: {subforum}")
        return redirect('archive:subforum-details', subforum_display_id=subforum_id, subforumslug=subforum.slug)
    except (ValueError, ArchiveTopic.DoesNotExist):
        return redirect('archive:index')
    
def prefill_new_post(request):
    if request.method == "POST":
        return HttpResponse(status=403)
        topic_id = request.GET.get("t")
        prefill_text = request.POST.get("prefill", "")
        request.session["prefill_message"] = prefill_text
        return redirect(f"{reverse('archive:new-post')}?t=" + topic_id)
    else:
        return redirect("archive:index")
    
def viewonline(request): 
    return render(request, "archive/viewonline.html")

@ratelimit(key='user_or_ip', method=['GET'], rate='10/m')
def removevotes(request, pollid):
    try:
        poll = ArchivePoll.objects.get(id=pollid)
    except ArchivePoll.DoesNotExist:
        return error_page(request, "Informations", "Ce sondage n'existe pas.")

    if poll is None:
        return error_page(request, "Informations", "Ce sondage n'existe pas.")
    
    if poll.is_active == False:
        return error_page(request, "Informations", "Ce sondage n'est plus actif.")
    return redirect('archive:login-view')