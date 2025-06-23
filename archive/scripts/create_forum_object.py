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

ArchiveForum.objects.get_or_create(
    name="UTF",
    total_users=1931,
    total_messages=28344,
    online_record=55,
    online_record_date=datetime(2024, 3, 29, 22, 59, tzinfo=ZoneInfo("Etc/GMT-1"))
)