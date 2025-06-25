import sys
import os
import django
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')
django.setup()

def run_population_script():
    """
    Orchestrates the deletion and population of the archive database by running
    various scripts in a specific order.
    """
    start_time = time.time()

    print("--- Starting database population process ---")

    # --- DELETION SCRIPTS ---
    print("\n--- Running deletion scripts ---")

    # 1. Delete all posts
    print("\n[1/16] Running delete_all_posts...")
    from delete_all_posts import delete_all_archive_posts
    delete_all_archive_posts()

    # 2. Delete all topics
    print("\n[2/16] Running delete_all_topics...")
    from delete_all_topics import delete_all_archive_topics
    delete_all_archive_topics()

    # 3. Delete all profiles
    print("\n[3/16] Running delete_all_profiles...")
    try:
        from delete_all_profiles import delete_all_archive_profiles
        delete_all_archive_profiles()
    except ImportError:
        print("Could not import 'delete_all_profiles.py'. Skipping.")
    except Exception as e:
        print(f"An error occurred while running delete_all_profiles: {e}")

    # 4. Delete all categories
    print("\n[4/16] Running delete_all_categories...")
    from delete_all_categories import delete_all_archive_categories
    delete_all_archive_categories()

    # 5. Delete all groups
    print("\n[5/16] Running delete_all_groups...")
    from delete_all_groups import delete_all_archive_groups
    delete_all_archive_groups()

    # 6. Delete all fake users
    print("\n[6/16] Running delete_all_fakeusers...")
    # The function in delete_all_fakeusers.py is misnamed 'delete_all_archive_profiles'.
    # It is aliased here to avoid conflicts and for clarity.
    from delete_all_fakeusers import delete_all_archive_profiles as delete_all_fake_users
    delete_all_fake_users()

    # 7. Delete forum
    print("\n[7/16] Running delete_forum...")
    from delete_forum import delete_forum
    delete_forum()

    # --- CREATION SCRIPTS ---
    print("\n--- Running creation scripts ---")

    # 8. Create forum object
    print("\n[8/16] Running create_arcForum_object...")
    import archive.scripts.create_forum_object as create_forum_object

    # 9. Create category objects
    print("\n[9/16] Running create_arcCateg_objects...")
    import archive.scripts.create_categ_objects as create_categ_objects

    # 10. Create group objects
    print("\n[10/16] Running create_arcGroups_objects...")
    import archive.scripts.create_groups_objects as create_groups_objects

    # 11. Create fake user objects
    print("\n[11/16] Running create_fakeuser_objects...")
    import create_fakeuser_objects

    # 12. Create profile objects
    print("\n[12/16] Running create_arcProfile_objects...")
    import archive.scripts.create_profile_objects as create_profile_objects

    # 13. Create subforum objects
    print("\n[13/16] Running create_arcSubforums...")
    import archive.scripts.create_subforums as create_subforums

    # 14. Create topic objects
    print("\n[14/16] Running create_arcTopics...")
    import archive.scripts.create_topics_objects as create_topics_objects

    # 15. Create post objects
    print("\n[15/16] Running create_arcPosts...")
    import archive.scripts.create_post_objects as create_post_objects

    # 15. Update forum object
    print("\n[16/16] Running update_forum...")
    import archive.scripts.update_forum as update_forum

    end_time = time.time()
    print(f"\n--- Population script finished in {end_time - start_time:.2f} seconds. ---")


if __name__ == "__main__":
    run_population_script()