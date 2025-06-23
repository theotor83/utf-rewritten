import sys
import os
import django
import json
from datetime import datetime, timedelta, timezone
from django.core.exceptions import ObjectDoesNotExist
from zoneinfo import ZoneInfo

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

django.setup()

from archive.models import FakeUser, ArchiveForumGroup, ArchiveProfile, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, ArchivePollOptionVoters, ArchiveSubforum

script_dir = os.path.dirname(__file__)
json_path = os.path.join(script_dir, "posts_data.json")


with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)


def create_post_object(data_object):
    if not FakeUser.objects.filter(id=data_object["author"]).exists():
        print(f"User with id {data_object['author']} does not exist, skipping post creation.")
        return
    if not ArchiveTopic.objects.filter(id=data_object["topic"]).exists():
        print(f"Parent topic with id {data_object['topic']} does not exist, skipping post creation.")
        return
    author_instance = FakeUser.objects.get(id=data_object["author"])
    parent_topic = ArchiveTopic.objects.get(id=data_object['topic'])
    if parent_topic.is_sub_forum:
        print(f"Parent topic {parent_topic.title} (id {data_object['topic']}) is a sub-forum, skipping post creation.")
        return
    
    aware_created_time = data_object["created_time"] # Already in UTC, no need to convert

    new_post = ArchivePost.objects.get_or_create(
        id = data_object["id"],
        author = author_instance,
        topic = parent_topic,
        text = data_object["text"],
        created_time = aware_created_time,
        updated_time = None,
        update_count = 0,
    )
    if not new_post[1]:
        print(f"Post id {data_object['id']} already exists, skipping creation.")
        return


def populate_posts():
    for i in range(len(data)):
        if i % 100 == 0:
            print(f"Processing post {i + 1}/{len(data)}")
        # Create ArchiveTopic object    
        create_post_object(data[i])

populate_posts()
