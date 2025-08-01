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

standard_datetime = make_timezone_aware("2016-03-24T12:00:00", 1)

ArchiveForumGroup.objects.get_or_create(name="Outsider", defaults={
    "priority": 10,
    "description": "Membres ne s'étant pas encore présentés.\nNombre de messages : 0.",
    "is_messages_group": True,
    "minimum_messages": 0,
    "color": "#847B7E",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Fallen Child", defaults={
    "priority": 20,
    "description": "Nouveaux sur le forum.\nNombre de messages : de 1 à 49.",
    "is_messages_group": True,
    "minimum_messages": 1,
    "color": "#FFFFFF",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="You're blue now !", defaults={
    "priority": 30,
    "description": "That's my attack !\nNombre de messages : de 50 à 199.",
    "is_messages_group": True,
    "minimum_messages": 50,
    "color": "#859BFD",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Made of Fire", defaults={
    "priority": 40,
    "description": "Membres confirmés.\nNombre de messages : de 200 à 999.",
    "is_messages_group": True,
    "minimum_messages": 200,
    "color": "#EA8C14",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Real Spider", defaults={
    "priority": 50,
    "description": "[color=#993399]I heard they like posting~[/color]\n\nMembres assidus.\nNombre de messages : de 1000 à 2999.",
    "is_messages_group": True,
    "minimum_messages": 1000,
    "color": "#8F1C93",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="It's showtime !", defaults={
    "priority": 60,
    "description": "Membres d'honneur.\nNombre de messages : de 2000 à 4999.",
    "is_messages_group": True,
    "minimum_messages": 2000,
    "color": "#F4D400",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Hopeful Dreamer", defaults={
    "priority": 70,
    "description": "Membre, euh... TRÈS déterminé ?\nNombre de messages : 5000 ou plus.",
    "is_messages_group": True,
    "minimum_messages": 5000,
    "color": "#FF00CC",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Royal Guard Apprentice", defaults={
    "priority": 80,
    "description": "Modérateurs ChatBox.",
    "is_messages_group": False,
    "minimum_messages": 999999,
    "color": "#2D3EDF",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Royal Guard", defaults={
    "priority": 90,
    "description": "Make her a member of the Royal Guard ♫\n\nModérateurs Forum.",
    "is_messages_group": False,
    "is_staff_group": False,
    "minimum_messages": 999999,
    "color": "#289331",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Determination", defaults={
    "priority": 100,
    "description": "Administrateurs.",
    "is_messages_group": False,
    "is_staff_group": True,
    "minimum_messages": 999999,
    "color": "#C02200",
    "created_at": standard_datetime
})

ArchiveForumGroup.objects.get_or_create(name="Gaster's follower", defaults={
    "priority": 110,
    "description": "Gaster followers.",
    "is_messages_group": False,
    "is_staff_group": False,
    "minimum_messages": 999999,
    "color": "#000000",
    "created_at": standard_datetime,
    "is_hidden": True
})

ArchiveForumGroup.objects.get_or_create(name="UTFbot", defaults={
    "priority": 120,
    "description": "UTFbot.",
    "is_messages_group": False,
    "is_staff_group": False,
    "minimum_messages": 999999,
    "color": "#6775AC",
    "created_at": standard_datetime,
    "is_hidden": True
})
