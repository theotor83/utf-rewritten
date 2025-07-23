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
json_path = os.path.join(script_dir, "topics_data.json")


with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)


def create_topic_object(data_object):
    if not FakeUser.objects.filter(id=data_object["author"]).exists():
        print(f"User with id {data_object['author']} does not exist, skipping topic creation.")
        return
    if data_object["parent_display_id"] and not ArchiveTopic.objects.filter(display_id=data_object["parent_display_id"]).exists():
        print(f"Parent topic with display_id {data_object['parent_display_id']} does not exist, skipping topic creation.")
        return
    author_instance = FakeUser.objects.get(id=data_object["author"])
    parent_subforum = None
    if data_object["parent_display_id"]:
        parent_subforum = ArchiveTopic.objects.get(display_id=data_object['parent_display_id'])
    if not data_object["category"] and parent_subforum:
        parent_category = parent_subforum.category
        if not parent_category:
            print(f"Parent category for topic with display_id {data_object['parent_display_id']} does not exist, skipping topic creation.")
            return
    else:
        print(f"Creating topic {data_object['title']} in category {data_object['category']}")
        parent_category = ArchiveCategory.objects.filter(id=data_object['category']).first()
        if not parent_category:
            print(f"Category {data_object['category']} does not exist, skipping topic creation.")
            return

    is_moved = data_object.get("moved", False) # Default to False if not present
    if is_moved:
        print(f"Topic {data_object['title']} ({data_object['id']}) is moved, skipping creation.")
        return
    
    aware_created_time = data_object["created_time"] # Already in UTC, no need to convert
    aware_last_message_time = data_object["last_message_time"] # Already in UTC, no need to convert

    new_topic = ArchiveTopic.objects.get_or_create(
        id = data_object["id"],
        author = author_instance,
        title = data_object["title"],
        description = data_object["description"],
        icon = data_object["icon"],
        slug = data_object["slug"],
        created_time = aware_created_time,
        last_message_time = aware_last_message_time,
        total_children = 0,
        total_replies = 0,
        total_views = 0,

        category = parent_category,
        parent = parent_subforum,

        is_sub_forum = data_object["is_sub_forum"],
        is_locked = data_object["is_locked"],
        is_pinned = data_object["is_pinned"],
        is_announcement = data_object["is_announcement"],
        is_index_topic = data_object["is_index_topic"],
        moved = is_moved,

        display_id=-1, # This will cause a MultipleObjectsReturned on line for parent_subforum
        display_children=data_object["total_children"],
        display_replies=data_object["total_replies"],
        display_views=data_object["total_views"],
    )
    if not new_topic[1]:
        print(f"Topic titled {data_object['title']} (id {data_object['id']}) already exists, skipping creation.")
        return


def populate_topics():
    for i in range(len(data)):
        if i % 100 == 0:
            print(f"Processing topic {i + 1}/{len(data)}")
        # Create ArchiveTopic object    
        create_topic_object(data[i])

populate_topics()
