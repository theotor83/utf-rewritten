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

from archive.models import FakeUser, ArchiveForumGroup, ArchiveProfile, ArchiveCategory, ArchivePost, ArchiveTopic, ArchiveForum, ArchiveTopicReadStatus, ArchiveSmileyCategory, ArchivePoll, ArchivePollOption, ArchiveSubforum

script_dir = os.path.dirname(__file__)
poll_json_path = os.path.join(script_dir, "polls_data.json")
poll_options_json_path = os.path.join(script_dir, "poll_options_data.json")



with open(poll_options_json_path, "r", encoding="utf-8") as file:
    poll_options_data = json.load(file)
with open(poll_json_path, "r", encoding="utf-8") as file:
    poll_data = json.load(file)


def create_poll_object(data_object):
    if not ArchiveTopic.objects.filter(id=data_object["topic"]).exists():
        print(f"Topic with id {data_object['topic']} does not exist, skipping poll creation.")
        return
    topic_instance = ArchiveTopic.objects.get(id=data_object['topic'])
    
    aware_created_at = data_object["created_at"] # Already in UTC, no need to convert

    new_poll = ArchivePoll.objects.get_or_create(
        id = data_object["id"],
        topic = topic_instance,
        question = data_object["question"],
        created_at = aware_created_at,
        max_choices_per_user = -1, # Always -1
        days_to_vote = 1, # Always 1 to prevent people from voting in the archive
        can_change_vote = 1 if data_object["can_change_vote"] else 0, # Convert boolean to integer
    )
    if not new_poll[1]:
        print(f"Poll with id {data_object['id']} already exists, skipping creation.")
        return


def populate_polls():
    for i in range(len(poll_data)):
        if i % 100 == 0:
            print(f"Processing poll {i + 1}/{len(poll_data)}")
        # Create ArchiveTopic object    
        create_poll_object(poll_data[i])





def create_poll_option_object(data_object):
    # Check if the referenced poll exists
    if not ArchivePoll.objects.filter(id=data_object["poll"]).exists():
        print(f"Poll with id {data_object['poll']} does not exist, skipping poll creation.")
        return

    # Check if all voters exist
    missing_voters = [v for v in data_object["voters"] if not FakeUser.objects.filter(id=v).exists()]
    if missing_voters:
        print(f"Voter(s) with ID(s) {missing_voters} do not exist, skipping poll creation.")
        return

    # Get the poll instance (foreign key)
    poll_instance = ArchivePoll.objects.get(id=data_object['poll'])

    # Create or get the ArchivePollOption
    new_poll_option, created = ArchivePollOption.objects.get_or_create(
        id= data_object["id"],
        poll=poll_instance,
        text=data_object["text"],
    )

    # If it already exists, skip
    if not created:
        print(f"Poll option with id {data_object['id']} already exists, skipping creation.")
        print(f"Details : Poll ID: {data_object['poll']}, Text: {data_object['text']}")
        return

    # Assign voters (many-to-many)
    voter_queryset = FakeUser.objects.filter(id__in=data_object["voters"])
    new_poll_option.voters.set(voter_queryset)


def populate_poll_options():
    for i in range(len(poll_options_data)):
        if i % 100 == 0:
            print(f"Processing poll option {i + 1}/{len(poll_options_data)}")
        # Create ArchiveTopic object    
        create_poll_option_object(poll_options_data[i])



def populate_everything():
    """
    Populates the database with all necessary data.
    """
    print("Populating polls...")
    populate_polls()
    
    print("Populating poll options...")
    populate_poll_options()

populate_everything()
