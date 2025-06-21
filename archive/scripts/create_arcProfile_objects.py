import sys
import os
import django
import json
from datetime import datetime, timedelta, timezone
from django.core.exceptions import ObjectDoesNotExist

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

django.setup()

from archive.models import FakeUser, ArchiveForumGroup, ArchiveProfile, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, ArchivePollOptionVoters, ArchiveSubforum

script_dir = os.path.dirname(__file__)
json_path = os.path.join(script_dir, "users_data.json")

def make_aware_with_offset(dt_str: str, offset_hours: int) -> datetime:
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


with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)


def create_profile_object(data_object):
    user_id_to_check = data_object["user"]["id"]
    if ArchiveProfile.objects.filter(user__id=user_id_to_check).exists():
        print(f"Profile for user {data_object['user']['id']} already exists, skipping.")
        return
    
    aware_last_login = make_aware_with_offset(data_object["last_login"], 0)
    aware_birthdate = make_aware_with_offset(data_object["birthdate"], 0)
    
    try:
        associated_user = FakeUser.objects.get(id=user_id_to_check)
    except ObjectDoesNotExist:
        print(f"The associated user with id {user_id_to_check} was not found.")
        return

    new_profile = ArchiveProfile.objects.create(
        user=associated_user,
        email_is_public=data_object["email_is_public"],
        messages_count=data_object["messages_count"],
        last_login=aware_last_login,
        website=data_object["website"],
        desc=data_object["desc"],
        localisation=data_object["localisation"],
        loisirs=data_object["loisirs"],
        birthdate=aware_birthdate,
        type=data_object["type"],
        favorite_games=data_object["favorite_games"],
        zodiac_sign=data_object["zodiac_sign"],
        gender=data_object["gender"],
        signature=data_object["signature"],
        profile_picture=data_object["profile_picture"],
        skype=data_object["skype"],

        display_id=data_object["user"]["display_id"],
        display_username=data_object["user"]["username"],
    )

    groups_to_add = []
    for group_data in data_object["groups"]:
        try:
            group_name = group_data["name"]
            group_obj = ArchiveForumGroup.objects.get(name=group_name)
            groups_to_add.append(group_obj)
        except ObjectDoesNotExist:
            print(f"Group '{group_data.get('name')}' not found, skipping for profile {new_profile.user.username}.")
        except KeyError:
            print(f"Group data in JSON is missing 'name' key: {group_data}")

    if groups_to_add:
        new_profile.groups.set(groups_to_add)

def populate_profiles():
    for i in range(len(data)):
        if i % 100 == 0:
            print(f"Processing profile {i + 1}/{len(data)}")
        # Create ArchiveProfile object    
        create_profile_object(data[i])

populate_profiles()
