import sys
import os
import django
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from utils import make_timezone_aware

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

django.setup()

from archive.models import FakeUser, ArchiveForumGroup, ArchiveProfile, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, ArchivePollOptionVoters, ArchiveSubforum

def make_awadre_with_offset(dt_str: str, offset_hours: int) -> datetime:
    offset = timezone(timedelta(hours=offset_hours))
    if not dt_str or dt_str.startswith("0000"): # Return default for empty or "0000-..." dates
        return datetime(2000, 1, 1, tzinfo=offset)
    try:
        naive_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    except (ValueError, OverflowError):
        print(f"Invalid date format for '{dt_str}', returning default date.")
        return datetime(2000, 1, 1, tzinfo=offset)

    # Dates from year 1 can cause OverflowError during timezone conversion by Django's ORM.
    if naive_dt.year < 2:
        print(f"Date '{dt_str}' is too early and would cause an overflow, returning default date.")
        return datetime(2000, 1, 1, tzinfo=offset)
    
    aware_dt = naive_dt.replace(tzinfo=offset)
    return aware_dt

# Available ids : 1, 2, 3, 4, 5, 6, 7, 8, 9, 21, 24, 27, 33, 34, 46, 57, 64

print("Checking if database is ready for subforums creation...")

tabbender = FakeUser.objects.get(username="Tabbender")
if not tabbender:
    print("Tabbender (admin) user not found, exiting script.")
    sys.exit(1)


ruins_category = ArchiveCategory.objects.get(slug="ruins")
if not ruins_category:
    print("Ruins category not found, exiting script.")
    sys.exit(1)

snowdin_category = ArchiveCategory.objects.get(slug="snowdin")
if not snowdin_category:
    print("Snowdin category not found, exiting script.")
    sys.exit(1)

waterfall_category = ArchiveCategory.objects.get(slug="waterfall")
if not waterfall_category:
    print("Waterfall category not found, exiting script.")
    sys.exit(1)

hotland_category = ArchiveCategory.objects.get(slug="hotland")
if not hotland_category:
    print("Hotland category not found, exiting script.")
    sys.exit(1)

surface_category = ArchiveCategory.objects.get(slug="surface")
if not surface_category:
    print("Surface category not found, exiting script.")
    sys.exit(1)


# ======== RUINS SUBFORUMS ========
print("Creating Ruins subforums...")


ArchiveTopic.objects.get_or_create(id=10000,
    author=tabbender,
    title="Règles du forum et Annonces",
    description="Les règles sont à lire avant de poster. Vous trouverez également les annonces du staff du forum.",
    #no icon,
    slug="r-gles-du-forum-et-annonces",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2016-08-13T18:22:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=ruins_category,
    #no parent,

    is_sub_forum=True,
    is_locked=True,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=8,
    display_children=2,
    display_replies=2,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10001,
    author=tabbender,
    title="Présentations",
    description="Se présenter est obligatoire pour pouvoir accéder au reste du forum.",
    #no icon,
    slug="pr-sentations",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2024-05-08T14:57:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=ruins_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=10,
    display_children=552,
    display_replies=7195,
    display_views=-1)


# ======== SNOWDIN SUBFORUMS ========
print("Creating Snowdin subforums...")


ArchiveTopic.objects.get_or_create(id=10002,
    author=tabbender,
    title="Aide et idées",
    description="Besoin d'aide ou conseils pour un passage du jeu ? Des choses à proposer pour tester en jeu ? C'est ici.",
    #no icon,
    slug="aide",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-10-03T22:31:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=snowdin_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=17,
    display_children=47,
    display_replies=484,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10003,
    author=tabbender,
    title="Tuto / Astuces",
    description="Si vous avez trouvé une astuce (permettant, par exemple, de faciliter une étape du jeu), vous pouvez partager ici.",
    #no icon,
    slug="tuto-astuces",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-06-03T23:28:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=snowdin_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=18,
    display_children=23,
    display_replies=224,
    display_views=-1)


# ======== WATERFALL SUBFORUMS ========
print("Creating Waterfall subforums...")


ArchiveTopic.objects.get_or_create(id=10004,
    author=tabbender,
    title="Easter eggs",
    description="Vous avez trouvé un easter egg, un secret (avec la fun value par exemple) ? Venez partager !",
    #no icon,
    slug="easter-eggs",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-11-14T09:08:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=waterfall_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=20,
    display_children=15,
    display_replies=166,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10005,
    author=tabbender,
    title="Espace technique",
    description="Tout ce qui concerne les fichiers du jeu, les mods, fichiers, etc.",
    #no icon,
    slug="espace-technique",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2024-04-16T09:33:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=waterfall_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=25,
    display_children=20,
    display_replies=195,
    display_views=-1)


# ======== HOTLAND SUBFORUMS ========
print("Creating Hotland subforums...")


ArchiveTopic.objects.get_or_create(id=10006,
    author=tabbender,
    title="Discussions générales",
    description="Parlez d'à peu près n'importe quoi en rapport avec les jeux.",
    #no icon,
    slug="autres",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-11-13T11:06:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=hotland_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=22,
    display_children=156,
    display_replies=2839,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10007,
    author=tabbender,
    title="Théories",
    description="Venez exposer des théories sur Undertale. Vérifiez que la théorie n'a pas déjà été postée. (Attention: Spoilers)",
    #no icon,
    slug="th-ories",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-05-03T23:19:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=hotland_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=14,
    display_children=88,
    display_replies=1214,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10008,
    author=tabbender,
    title="Fangames / Unitale",
    description="Venez parler de fangames en rapport avec Undertale, ou d'Unitale et ses scripts.",
    #no icon,
    slug="fangames-unitale",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-10-03T22:28:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=hotland_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=15,
    display_children=21,
    display_replies=266,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10009,
    author=tabbender,
    title="Médias",
    description="Undertale et son OST, ses fan-vidéos, images, YTPMV, shitposts, etc.",
    #no icon,
    slug="vid-os",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-05-03T23:22:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=hotland_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=16,
    display_children=57,
    display_replies=740,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10010,
    author=tabbender,
    title="Création",
    description="Pour tout ce que vous avez créé à propos d'Undertale.",
    #no icon,
    slug="cr-ation",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-10-03T22:30:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=hotland_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=32,
    display_children=103,
    display_replies=1331,
    display_views=-1)


# ======== SURFACE SUBFORUMS ========
print("Creating Surface subforums...")


ArchiveTopic.objects.get_or_create(id=10011,
    author=tabbender,
    title="Section libre",
    description="Parlez de (presque) tout ce que vous voulez ici (en dehors d'Undertale).",
    #no icon,
    slug="section-libre",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-11-13T11:04:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=11,
    display_children=176,
    display_replies=2464,
    display_views=-1)

jeux_instance = ArchiveTopic.objects.get_or_create(id=10012,
    author=tabbender,
    title="Jeux",
    description="Venez proposer vos jeux ou roleplays ici.",
    #no icon,
    slug="jeux",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2024-03-26T11:11:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    has_subforum_children=True,  # This will allow nested subforums
    
    display_id=12,
    display_children=93,
    display_replies=7867,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10013,
    author=tabbender,
    title="Membres",
    description="Tout ce qui est en rapport avec les membres de ce forum.",
    #no icon,
    slug="membres",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2024-05-08T14:59:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=28,
    display_children=50,
    display_replies=1347,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10014,
    author=tabbender,
    title="Sondages",
    description="Faites des sondages ! Pour les sondages sur Undertale allez plutôt dans la section discussions.",
    #no icon,
    slug="sondages",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2024-04-16T09:30:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=29,
    display_children=71,
    display_replies=1156,
    display_views=-1)

ArchiveTopic.objects.get_or_create(id=10015,
    author=tabbender,
    title="Pub",
    description="Venez présenter votre chaîne, site, etc... ici et nulle part ailleurs.",
    #no icon,
    slug="pub",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-06-03T23:43:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    #no parent,

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=True,
    
    display_id=13,
    display_children=76,
    display_replies=805,
    display_views=-1)





print("Creating nested subforum (roleplay)...")

ArchiveTopic.objects.get_or_create(id=10016,
    author=tabbender,
    title="RolePlay",
    description="Pour vos jeux de rôle.",
    #no icon,
    slug="rp",
    created_time=make_timezone_aware("2016-03-24T12:00:00", 1),
    last_message_time=make_timezone_aware("2023-11-19T21:56:00", 1),
    total_children=0,
    total_replies=0,
    total_views=0,

    category=surface_category,
    parent=jeux_instance[0],  # Use the instance returned by get_or_create

    is_sub_forum=True,
    is_locked=False,
    is_pinned=False,
    is_announcement=False,
    is_index_topic=False,
    
    display_id=31,
    display_children=54,
    display_replies=4628,
    display_views=-1)

print("Subforums created successfully.")