import sys
import os
import django
import json
from datetime import datetime, timedelta, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

django.setup()

from archive.models import FakeUser, ArchiveForumGroup, ArchiveProfile, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, ArchivePollOptionVoters, ArchiveSubforum

ArchiveCategory.objects.get_or_create(
    id=1,
    name="RUINS",
    slug="ruins",
)

ArchiveCategory.objects.get_or_create(
    id=2,
    name="Snowdin",
    slug="snowdin",
)

ArchiveCategory.objects.get_or_create(
    id=3,
    name="Waterfall",
    slug="waterfall",
)

ArchiveCategory.objects.get_or_create(
    id=4,
    name="Hotland",
    slug="hotland",
)

ArchiveCategory.objects.get_or_create(
    id=5,
    name="Surface",
    slug="surface",
)