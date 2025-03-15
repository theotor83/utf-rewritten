import locale
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, ProfileForm, NewTopicForm, NewPostForm, QuickReplyForm, MemberSortingForm, UserEditForm
from .models import Profile, ForumGroup, User, Category, Post, Topic, Forum, TopicReadStatus
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField, Q
from django.urls import reverse
from urllib.parse import urlencode

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

# Create your views here.

def index_redirect(request):
    return redirect("index")

def index(request):
    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    # Set the locale to French
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

    # Get the current time and format it
    now = timezone.localtime(timezone.now())
    formatted_date = now.strftime("%a %d %b - %H:%M (%Y)").title().replace(" 0", " ").replace(".","")

    categories = Category.objects.filter(is_hidden=False)
    
    # Process topics for each category
    for category in categories:
        # Get topics but don't use the queryset directly
        topics_list = list(category.index_topics.all())
        
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

    online = User.objects.filter(profile__last_login__gte=timezone.now() - timezone.timedelta(minutes=30))

    context = {
        'current_date': _(f"La date/heure actuelle est {formatted_date}"),
        "categories": categories,
        "utf":utf,
        "online":online,
    }

    return render(request, "index.html", context)

def faq(request):
    return render(request, "faq.html")

def register_regulation(request):
    return render(request, "register_regulation.html")

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
    return render(request, 'register.html', context)

def error_page(request, error_title, error_message):
    context = {"error_title":error_title, "error_message":error_message}
    return render(request, "error_page.html", context)

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("index")

def profile_details(request, userid):
    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    try :
        requested_user = User.objects.get(id=userid)
    except:
        return error_page(request, "Informations", "Désolé, mais cet utilisateur n'existe pas.")
    
    percentage = get_percentage(requested_user.profile.messages_count, utf.total_messages)
    context = {"req_user":requested_user, "percentage":percentage, "message_frequency":get_message_frequency(requested_user.profile.messages_count, requested_user.date_joined)}
    return render(request, "profile_page.html", context)
    
def member_list(request):
    members_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * members_per_page
    all_members = User.objects.filter(profile__isnull=False).order_by('-id')
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
            order_by_field = "username"
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
            members = User.objects.filter(profile__isnull=False).order_by('-profile__messages_count')[:10]  # Descending order + limit 10
            # Disable pagination for top10 mode
            pagination = []

        # Apply ordering before slicing
        if order == "DESC":
            order_by_field = f"-{order_by_field}"  # Prefix with '-' for descending order
        
        if members is None:
            # Only apply pagination for non-topten modes
            if custom_filter is not None:
                members = User.objects.filter(profile__isnull=False, **custom_filter).order_by(order_by_field)[limit - members_per_page : limit]
            else:
                members = User.objects.filter(profile__isnull=False).order_by(order_by_field)[limit - members_per_page : limit]



    context =  {"members" : members, "current_page" : current_page, "max_page":max_page, "pagination":pagination, "form":form}

    return render(request, "memberlist.html", context)

def subforum_details(request, subforumid, subforumslug):
    try:
        subforum = Topic.objects.get(id=subforumid)
    except:
        error_page(request,"Erreur","jsp")

    topics_per_page = min(int(request.GET.get('per_page', 50)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * topics_per_page
    all_topics = Topic.objects.filter(parent=subforum, is_sub_forum=False)
    all_subforums = Topic.objects.filter(parent=subforum, is_sub_forum=True)
    announcement_topics = Topic.objects.filter(is_announcement=True)
    count = all_topics.count()
    max_page = (count + topics_per_page - 1) // topics_per_page

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

    context = {"announcement_topics":announcement_topics, "topics":topics, "subforum":subforum, "tree":tree, "all_subforums":all_subforums} 
    return render(request, 'subforum_details.html', context)

def test_page(request):
    return render(request, "search.html")

def new_topic(request):
    subforum_id = request.GET.get('f')
    subforum = Topic.objects.get(id=subforum_id)
    if subforum == None or subforum.is_sub_forum == False:
        return error_page(request, "Erreur", "Une erreur est survenue lors de la création du sujet.")

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
                    return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.")
                else:
                    # Check if the user is "Outsider" as top group
                    top_group = user_profile.get_top_group
                    if top_group.name == "Outsider":
                        return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.")
            except Profile.DoesNotExist:
                return error_page(request, "Informations", "Vous devez vous présenter avant de créer un sujet.")

    if request.method == 'POST':
        form = NewTopicForm(request.POST, user=request.user, subforum=subforum)
        if form.is_valid():
            new_topic = form.save()
            return redirect(topic_details, new_topic.id, new_topic.slug)
    else:
        form = NewTopicForm(user=request.user, subforum=subforum)

    return render(request, 'new_topic_form.html', {'form': form, 'subforum': subforum, "tree":tree})

def topic_details(request, topicid, topicslug):
    try:
        topic = Topic.objects.get(id=topicid)        
        if request.user.is_authenticated:
            TopicReadStatus.objects.update_or_create( user=request.user, topic=topic, defaults={'last_read': timezone.now()})  # Mark the topic as read for the user
    except Topic.DoesNotExist:
        return error_page(request, "Erreur", "Ce sujet n'existe pas.")

    subforum = topic.parent

    posts_per_page = min(int(request.GET.get('per_page', 15)),250)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * posts_per_page
    all_posts = Post.objects.filter(topic=topic)
    count = all_posts.count()
    max_page = (count + posts_per_page - 1) // posts_per_page

    posts = all_posts.order_by('created_time')[limit - posts_per_page : limit]

    pagination = generate_pagination(current_page, max_page)

    tree = topic.get_tree
    # for i in tree:
    #     print(f" tree : {tree}")
    
    #if posts.count() <= 0:
    #    return error_page(request, "Erreur","Ce sujet n'a pas de messages.")

    if request.method == 'POST':
        form = QuickReplyForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            new_post = form.save()
            return redirect(topic_details, topic.id, topic.slug)
    else:
        form = QuickReplyForm(user=request.user, topic=topic)

    render_quick_reply = True

    if request.user.is_authenticated == False:
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
    context = {"posts": posts, "tree":tree, "topic":topic, "subforum":subforum, "form":form, "pagination":pagination,"current_page" : current_page, "max_page":max_page,"render_quick_reply":render_quick_reply}
    return render(request, 'topic_details.html', context)

def new_post(request):
    topic_id = request.GET.get('t')
    topic = Topic.objects.get(id=topic_id)
    if topic == None or topic.is_locked:
        if request.user.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.")
        
    if topic.is_sub_forum:
        if request.user.is_user_staff == False:
            return error_page(request, "Informations", "Vous ne pouvez pas répondre à ce sujet.")

    tree = topic.get_tree

    if request.user.is_authenticated == False:
        return redirect("login-view")
    else:
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_groups = user_profile.groups.all()
            # Check if the user has no group
            if user_groups.count() == 0:
                return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.")
            else:
                # Check if the user is "Outsider" as top group
                top_group = user_profile.get_top_group
                if top_group.name == "Outsider":
                    return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.")
        except Profile.DoesNotExist:
            return error_page(request, "Informations", "Vous devez vous présenter avant de répondre à un sujet.")

    if request.method == 'POST':
        form = NewPostForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            new_post = form.save()
            return redirect(topic_details, topic.id, topic.slug)
    else:
        form = NewPostForm(user=request.user, topic=topic)
    
    return render(request, 'new_post_form.html', {'form': form, 'topic': topic, "tree":tree})

def category_details(request, categoryid, categoryslug): #TODO : [4] Add read status
    try:
        category = Category.objects.get(id=categoryid)
    except Category.DoesNotExist:
        return error_page(request, "Erreur", "Category not found")
    
    utf, created = Forum.objects.get_or_create(name='UTF')
    if created:
        print("Forum UTF created")
        utf.save()

    index_topics = category.index_topics.all()
    
    root_not_index_topics = Topic.objects.annotate(
        is_root=Case(
            When(parent__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).filter(is_root=True, category=category).exclude(id__in=index_topics.values_list('id', flat=True))

    context = {
        "category": category,
        "index_topics": index_topics,
        "root_not_index_topics": root_not_index_topics,
        "forum": utf
    }
    return render(request, "category_details.html", context)
    
    
def search(request):
    return render(request, "search.html")

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

            return error_page(request, "Informations", message)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'edit_profile.html', context)

def search_results(request):
    #Define custom filter and order by field
    custom_filter = Q()
    order_by_field = '-id'
    
    # Search query parameters
    order = request.GET.get('order', 'ASC')
    keyword = request.GET.get('keyword', '')
    author = request.GET.get('author', '')

    

    if order == "DESC":
            order_by_field = order_by_field[1:]  # Remove '-' for ascending order

    if keyword:
        custom_filter &= Q(text__icontains=keyword) | Q(topic__title__icontains=keyword)

    if author:
        custom_filter &= Q(author__username__exact=author)

    # Pagination query parameters
    messages_per_page = min(int(request.GET.get('per_page', 15)),75)
    current_page = int(request.GET.get('page', 1))
    limit = current_page * messages_per_page
    
    all_results = Post.objects.filter(custom_filter).order_by(order_by_field)
    result_count = all_results.count()
    results = all_results[limit - messages_per_page : limit]

    max_page = (result_count + messages_per_page - 1) // messages_per_page
    pagination = generate_pagination(current_page, max_page)


    context =  {"results" : results, "result_count" : result_count, "current_page" : current_page, "max_page":max_page, "pagination":pagination}
    return render(request, "search_results.html", context)