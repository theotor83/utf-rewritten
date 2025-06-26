import sys
import os
import django
from django.db import connections, ProgrammingError

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utf.settings')
django.setup()

# Import the model after setting up Django
from archive.models import ArchiveForumGroup

def delete_all_archive_groups():
    """
    Deletes all instances of ArchiveForumGroup from the database
    and resets the primary key sequence.
    """
    db_alias = 'archive'
    connection = connections[db_alias]
    table_name = ArchiveForumGroup._meta.db_table

    print("Deleting all ArchiveForumGroup instances...")
    try:
        with connection.cursor() as cursor:
            # Use raw SQL to delete all rows, which is faster and avoids model validation issues
            cursor.execute(f'DELETE FROM "{table_name}";')

            # Reset the ID sequence
            print(f"Resetting the ID sequence for table '{table_name}'...")
            if connection.vendor == 'sqlite':
                # For SQLite, deleting from sqlite_sequence resets the counter.
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
            elif connection.vendor == 'postgresql':
                # For PostgreSQL, use TRUNCATE ... RESTART IDENTITY
                cursor.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')
            
            # Since we can't get a row count from the above, we'll just confirm completion
            print(f"All instances from '{table_name}' have been deleted and sequence reset.")

    except ProgrammingError as e:
        # This can happen if the table doesn't exist, etc.
        print(f"Could not delete from '{table_name}': {e}")
        print("This may happen if the table does not exist, which is usually fine.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    delete_all_archive_groups()