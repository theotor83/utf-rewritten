import sys
import os
import django
from django.db import connections

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')
django.setup()

# Import the model after setting up Django
from archive.models import ArchiveTopic

def delete_all_archive_topics():
    """
    Deletes all instances of ArchiveTopic from the database
    and resets the primary key sequence for SQLite.
    """
    db_alias = 'archive'
    table_name = ArchiveTopic._meta.db_table

    # First, delete all the objects using the ORM.
    print("Deleting all ArchiveTopic instances...")
    count, _ = ArchiveTopic.objects.using(db_alias).all().delete()
    print(f"{count} ArchiveTopic instances have been deleted.")

    # Now, reset the sequence counter using raw SQL.
    print(f"Resetting the ID sequence for table '{table_name}'...")
    
    # Use the 'archive' database connection
    with connections[db_alias].cursor() as cursor:
        # For SQLite, deleting from sqlite_sequence resets the counter.
        try:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
            print(f"ID sequence for '{table_name}' has been reset.")
        except Exception as e:
            print(f"Could not reset sequence for '{table_name}': {e}")
            print("This may happen if the table was already empty, which is usually fine.")

if __name__ == "__main__":
    delete_all_archive_topics()