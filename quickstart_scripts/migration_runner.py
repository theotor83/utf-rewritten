"""
Migration runner for Django project quickstart.
Handles database migrations for both main and archive databases.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_django_command(command_args, description):
    """
    Run a Django management command.
    
    Args:
        command_args: List of command arguments
        description: Description of the command for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    project_dir = Path(__file__).parent.parent
    manage_py = project_dir / "manage.py"
    
    if not manage_py.exists():
        print(f"❌ manage.py not found in {project_dir}")
        return False
    
    print(f"🔄 {description}...")
    
    try:
        # Build the full command
        full_command = [sys.executable, str(manage_py)] + command_args
        
        # Run the command
        result = subprocess.run(
            full_command,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during {description.lower()}: {e}")
        return False

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(__file__).parent.parent / ".env"
    return env_path.exists()

def run_migrations():
    """
    Run Django migrations for both main and archive databases.
    
    Returns:
        bool: True if all migrations successful, False otherwise
    """
    print("🗃️  Database Migration Runner")
    print("=" * 35)
    
    # Check if .env file exists
    if not check_env_file():
        print("⚠️  Warning: .env file not found!")
        print("   Some database settings might not be configured.")
        print("   Proceeding with default settings...")
    
    # Step 1: Make migrations
    print("\n📝 Creating migration files...")
    if not run_django_command(["makemigrations"], "Making migrations"):
        print("⚠️  makemigrations failed, but this might be normal if no changes detected")
        print("   Continuing with existing migrations...")
    
    # Step 2: Apply migrations to main database
    print("\n🗄️  Applying migrations to main database...")
    if not run_django_command(["migrate"], "Migrating main database"):
        print("❌ Main database migration failed!")
        return False
    
    # Step 3: Apply migrations to archive database
    print("\n📚 Applying migrations to archive database...")
    if not run_django_command(["migrate", "--database=archive"], "Migrating archive database"):
        print("❌ Archive database migration failed!")
        return False
    
    print("\n✅ All database migrations completed successfully!")
    
    # Optional: Show migration status
    try:
        print("\n📊 Migration Status:")
        print("Main database:")
        subprocess.run([sys.executable, "manage.py", "showmigrations"], 
                      cwd=Path(__file__).parent.parent, timeout=10)
        
        print("\nArchive database:")
        subprocess.run([sys.executable, "manage.py", "showmigrations", "--database=archive"], 
                      cwd=Path(__file__).parent.parent, timeout=10)
    except Exception:
        pass  # Non-critical, just skip if it fails
    
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
