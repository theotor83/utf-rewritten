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

    # 1. Delete all topics
    print("\n[1/12] Running delete_all_topics...")
    from delete_all_topics import delete_all_archive_topics
    delete_all_archive_topics()

    # 2. Delete all profiles
    print("\n[2/12] Running delete_all_profiles...")
    try:
        from delete_all_profiles import delete_all_archive_profiles
        delete_all_archive_profiles()
    except ImportError:
        print("Could not import 'delete_all_profiles.py'. Skipping.")
    except Exception as e:
        print(f"An error occurred while running delete_all_profiles: {e}")

    # 3. Delete all categories
    print("\n[3/12] Running delete_all_categories...")
    from delete_all_categories import delete_all_archive_categories
    delete_all_archive_categories()

    # 4. Delete all groups
    print("\n[4/12] Running delete_all_groups...")
    from delete_all_groups import delete_all_archive_groups
    delete_all_archive_groups()

    # 5. Delete all fake users
    print("\n[5/12] Running delete_all_fakeusers...")
    # The function in delete_all_fakeusers.py is misnamed 'delete_all_archive_profiles'.
    # It is aliased here to avoid conflicts and for clarity.
    from delete_all_fakeusers import delete_all_archive_profiles as delete_all_fake_users
    delete_all_fake_users()

    # 6. Delete forum
    print("\n[6/12] Running delete_forum...")
    from delete_forum import delete_forum
    delete_forum()

    # --- CREATION SCRIPTS ---
    print("\n--- Running creation scripts ---")

    # 7. Create forum object
    print("\n[7/12] Running create_arcForum_object...")
    import create_arcForum_object

    # 8. Create category objects
    print("\n[8/12] Running create_arcCateg_objects...")
    import create_arcCateg_objects

    # 9. Create group objects
    print("\n[9/12] Running create_arcGroups_objects...")
    import create_arcGroups_objects

    # 10. Create fake user objects
    print("\n[10/12] Running create_fakeuser_objects...")
    import create_fakeuser_objects

    # 11. Create profile objects
    print("\n[11/12] Running create_arcProfile_objects...")
    import create_arcProfile_objects

    # 12. Create subforum objects
    print("\n[12/12] Running create_arcSubforums...")
    import create_arcSubforums

    end_time = time.time()
    print(f"\n--- Population script finished in {end_time - start_time:.2f} seconds. ---")


if __name__ == "__main__":
    run_population_script()