import os
import sys
import django
from django.conf import settings
from django.core.files.images import ImageFile
from django.contrib.staticfiles import finders

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")

# Mapping of group names to their corresponding icon filenames.
group_name_to_icon_filename = {
    "Fallen Child": "gicon_fallen_child.png",
    "You're blue now !": "gicon_youre_blue_now.png",
    "Made of Fire": "gicon_made_of_fire.png",
    "Real Spider": "gicon_real_spider.png",
    "It's showtime !": "gicon_its_showtime.png",
    "Hopeful Dreamer": "gicon_hopeful_dreamer.png",
    "Royal Guard Apprentice": "gicon_royal_guard_apprentice.png",
    "Royal Guard": "gicon_royal_guard.png",
    "Determination": "gicon_determination.png",
}

def populate_group_icons():
    """
    Updates the icon for each ArchiveForumGroup based on a predefined mapping.
    """
    print("Starting the group icon update script...")

    try:
        from archive.models import ArchiveForumGroup
    except ImportError:
        print("[Error] Could not import the 'ArchiveForumGroup' model from the 'archive' app.")
        return

    instances = ArchiveForumGroup.objects.all()
    print(f"Found {instances.count()} groups to process.")

    for instance in instances:
        group_name = instance.name
        icon_filename = group_name_to_icon_filename.get(group_name)

        if icon_filename:
            # Construct the relative path to the icon within the static files.
            relative_path = os.path.join('images', 'group_icons', icon_filename)
            absolute_image_path = finders.find(relative_path)

            if not absolute_image_path:
                print(f"[Warning] Could not find static file for group '{group_name}': '{relative_path}'. Skipping.")
                continue

            try:
                with open(absolute_image_path, 'rb') as f:
                    image = ImageFile(f, name=icon_filename)
                    instance.icon = image
                    instance.save()
                    print(f"Successfully updated icon for group '{group_name}'.")
            except IOError as e:
                print(f"[Error] Could not open or read the image file for group '{group_name}': {e}. Skipping.")
        else:
            print(f"[Warning] No icon mapping found for group '{group_name}'. Skipping.")

    print("\nScript finished.")

if __name__ == "__main__":
    populate_group_icons()