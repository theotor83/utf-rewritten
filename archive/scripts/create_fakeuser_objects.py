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

script_dir = os.path.dirname(__file__)
json_path = os.path.join(script_dir, "users_data.json")

def make_aware_with_offset(dt_str: str, offset_hours: int) -> datetime:
    naive_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    offset = timezone(timedelta(hours=offset_hours))
    aware_dt = naive_dt.replace(tzinfo=offset)
    return aware_dt


with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)


def create_fakeuser_object(data_object):
    if FakeUser.objects.filter(id=data_object["user"]["id"]).exists():
        print(f"FakeUser with id {data_object['user']['id']} already exists, skipping.")
    else:
        aware_date_joined = make_aware_with_offset(data_object["user"]["date_joined"], 0)
        fake_user = FakeUser.objects.create(
            id=data_object["user"]["id"],
            username=data_object["user"]["username"],
            email=data_object["user"]["email"],
            is_staff=False,
            is_active=False,
            date_joined=aware_date_joined,
            is_authenticated=False,
        )
        #print(f"Created FakeUser: {fake_user.username}")

def populate_fakeusers():
    for i in range(len(data)):
        if i % 100 == 0:
            print(f"Processing user {i + 1}/{len(data)}")
        # Create FakeUser object    
        create_fakeuser_object(data[i])

