"""
Environment file creator for Django project quickstart.
Handles .env file creation with user preferences and validation.
"""

import os
import secrets
import string
from pathlib import Path

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default value."""
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please enter a value.")

def get_yes_no(prompt, default="n"):
    """Get yes/no input from user."""
    valid = {"yes": True, "y": True, "no": False, "n": False, "true": True, "false": False}
    if default.lower() == "y" or default.lower() == "true":
        prompt += " [Y/n]"
        default_bool = True
    else:
        prompt += " [y/N]"
        default_bool = False
    
    while True:
        choice = input(prompt + ": ").lower().strip()
        if choice == "":
            return default_bool
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes', 'no', 'y', 'n', 'true', or 'false'.")

def generate_random_password(length=16):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_secret_key():
    """Generate Django secret key."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*(-_=+)') for _ in range(50))

def validate_configuration(config, mode):
    """Validate configuration for potential issues."""
    warnings = []
    
    if mode == "production":
        if config.get("DEBUG") == "True":
            warnings.append("DEBUG=True is not recommended for production")
        if config.get("DEVELOPMENT_MODE") == "True":
            warnings.append("DEVELOPMENT_MODE=True is not recommended for production")
        if config.get("LOCALHOST_DOCKER") == "True":
            warnings.append("LOCALHOST_DOCKER=True is not recommended for production")
        if config.get("DJANGO_DEBUG_TOOLBAR_ENABLED") == "True":
            warnings.append("DJANGO_DEBUG_TOOLBAR_ENABLED=True is not recommended for production")
    
    return warnings

def backup_existing_env():
    """Backup existing .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        return True
    
    print("⚠️  An existing .env file was found!")
    if not get_yes_no("Do you want to backup the existing .env file?", "y"):
        if not get_yes_no("Are you sure you want to overwrite the existing .env file?", "n"):
            print("Setup cancelled.")
            return False
    
    # Find a suitable backup name
    counter = 0
    while True:
        if counter == 0:
            backup_name = "old.env"
        else:
            backup_name = f"old({counter}).env"
        
        backup_path = env_path.parent / backup_name
        if not backup_path.exists():
            break
        counter += 1
    
    try:
        env_path.rename(backup_path)
        print(f"✅ Existing .env backed up as {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup .env file: {e}")
        return False

def create_env_file():
    """
    Create .env file with user preferences.
    
    Returns:
        bool: True if creation successful, False otherwise
    """
    print("🔧 Environment Configuration Setup")
    print("=" * 40)
    
    # Backup existing .env if needed
    if not backup_existing_env():
        return False
    
    # Get deployment mode
    print("\n📍 Deployment Mode Selection:")
    print("1. Development (local machine)")
    print("2. Production (remote server)")
    
    while True:
        mode_choice = input("Select mode [1/2]: ").strip()
        if mode_choice == "1":
            mode = "development"
            break
        elif mode_choice == "2":
            mode = "production"
            break
        else:
            print("Please enter 1 or 2.")
    
    print(f"\n🎯 Selected: {mode.title()} mode")
    
    # Get configuration mode
    print("\n⚙️  Configuration Mode:")
    print("1. Simple (recommended settings with minimal input)")
    print("2. Advanced (full customization)")
    
    while True:
        config_choice = input("Select configuration mode [1/2]: ").strip()
        if config_choice == "1":
            simple_mode = True
            break
        elif config_choice == "2":
            simple_mode = False
            break
        else:
            print("Please enter 1 or 2.")
    
    config = {}
    
    # Basic settings
    print(f"\n🔑 Basic Configuration:")
    config["SECRET_KEY"] = generate_secret_key()
    print("✅ Generated Django secret key")
    
    if simple_mode:
        # Simple mode with recommended defaults
        if mode == "development":
            config["DEBUG"] = "True"
            config["DEVELOPMENT_MODE"] = "True"
            config["LOCALHOST_DOCKER"] = "True"
            config["DJANGO_DEBUG_TOOLBAR_ENABLED"] = "True"
            config["USE_REDIS_IN_DEV"] = "False"
        else:  # production
            config["DEBUG"] = "False"
            config["DEVELOPMENT_MODE"] = "False"
            config["LOCALHOST_DOCKER"] = "False"
            config["DJANGO_DEBUG_TOOLBAR_ENABLED"] = "False"
            config["USE_REDIS_IN_DEV"] = "False"
        
        print(f"✅ Applied {mode} defaults")
    else:
        # Advanced mode - ask for each setting
        print("🔧 Advanced Configuration:")
        config["DEBUG"] = "True" if get_yes_no("Enable DEBUG mode", "y" if mode == "development" else "n") else "False"
        config["DEVELOPMENT_MODE"] = "True" if get_yes_no("Enable DEVELOPMENT_MODE", "y" if mode == "development" else "n") else "False"
        config["LOCALHOST_DOCKER"] = "True" if get_yes_no("Enable LOCALHOST_DOCKER", "y" if mode == "development" else "n") else "False"
        config["DJANGO_DEBUG_TOOLBAR_ENABLED"] = "True" if get_yes_no("Enable Django Debug Toolbar", "y" if mode == "development" else "n") else "False"
        config["USE_REDIS_IN_DEV"] = "True" if get_yes_no("Use Redis in development", "y" if mode == "development" else "n") else "False"
    
    # Admin password
    print(f"\n👤 Admin Configuration:")
    use_random_admin = get_yes_no("Generate random admin password", "y")
    if use_random_admin:
        config["ADMIN_PASSWORD"] = generate_random_password(20)
        print("✅ Generated random admin password")
    else:
        config["ADMIN_PASSWORD"] = get_user_input("Enter admin password")
    
    # Allowed hosts
    if mode == "development":
        config["DJANGO_ALLOWED_HOSTS"] = "localhost,127.0.0.1"
    else:
        additional_hosts = get_user_input("Enter additional allowed hosts (comma-separated)", "", required=False)
        if additional_hosts:
            # Always include localhost and 127.0.0.1, then add user-specified hosts
            config["DJANGO_ALLOWED_HOSTS"] = f"localhost,127.0.0.1,{additional_hosts}"
        else:
            config["DJANGO_ALLOWED_HOSTS"] = "localhost,127.0.0.1"
    
    # Database configuration
    print(f"\n🗄️  Database Configuration:")
    print("Note: Database URLs are required and must be configured manually")
    
    # PostgreSQL settings
    use_random_db_pass = get_yes_no("Generate random database passwords", "y")
    
    if use_random_db_pass:
        config["POSTGRES_USER"] = "postgres"
        config["POSTGRES_PASSWORD"] = generate_random_password(16)
        config["POSTGRES_DB"] = "utf_forum"
        
        config["ARCHIVE_POSTGRES_USER"] = "archive_user"
        config["ARCHIVE_POSTGRES_PASSWORD"] = generate_random_password(16)
        config["ARCHIVE_POSTGRES_DB"] = "utf_archive"
        print("✅ Generated random database passwords")
    else:
        config["POSTGRES_USER"] = get_user_input("PostgreSQL username", "postgres")
        config["POSTGRES_PASSWORD"] = get_user_input("PostgreSQL password")
        config["POSTGRES_DB"] = get_user_input("PostgreSQL database name", "utf_forum")
        
        config["ARCHIVE_POSTGRES_USER"] = get_user_input("Archive PostgreSQL username", "archive_user")
        config["ARCHIVE_POSTGRES_PASSWORD"] = get_user_input("Archive PostgreSQL password")
        config["ARCHIVE_POSTGRES_DB"] = get_user_input("Archive PostgreSQL database name", "utf_archive")
    
    # Database URLs - these need manual configuration
    print("\n⚠️  IMPORTANT: Database URLs need manual configuration!")
    print("Default DATABASE_URL format: postgres://username:password@host:port/database")
    
    config["DATABASE_URL"] = f"postgres://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@db:5432/{config['POSTGRES_DB']}"
    config["ARCHIVE_DATABASE_URL"] = f"postgres://{config['ARCHIVE_POSTGRES_USER']}:{config['ARCHIVE_POSTGRES_PASSWORD']}@db:5432/{config['ARCHIVE_POSTGRES_DB']}"
    
    print("📝 Using default database URL format with Docker service name 'db'")
    print("   You may need to adjust the host (db) depending on your setup")
    
    # Redis configuration
    print(f"\n🔴 Redis Configuration:")
    use_random_redis = get_yes_no("Generate random Redis password", "y")
    if use_random_redis:
        config["REDIS_PASSWORD"] = generate_random_password(16)
        print("✅ Generated random Redis password")
    else:
        config["REDIS_PASSWORD"] = get_user_input("Enter Redis password")
    
    # User restrictions
    print(f"\n👥 User Management:")
    config["RESTRICT_NEW_USERS"] = "True" if get_yes_no("Restrict newly created users (force them to present themselves)", "n") else "False"
    
    # Validate configuration
    warnings = validate_configuration(config, mode)
    if warnings:
        print(f"\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   • {warning}")
        
        if not get_yes_no("Do you want to continue with these settings", "y"):
            print("Configuration cancelled.")
            return False
    
    # Write .env file
    try:
        env_path = Path(__file__).parent.parent / ".env"
        with open(env_path, 'w') as f:
            f.write('# Django Project Environment Configuration\n')
            f.write(f'# Generated in {mode} mode\n')
            f.write('# ==========================================\n\n')
            
            # Basic settings
            f.write('# Basic Django settings\n')
            f.write(f'SECRET_KEY="{config["SECRET_KEY"]}"\n')
            f.write(f'DEBUG={config["DEBUG"]}\n')
            f.write(f'DEVELOPMENT_MODE={config["DEVELOPMENT_MODE"]}\n')
            f.write(f'ADMIN_PASSWORD="{config["ADMIN_PASSWORD"]}"\n')
            f.write(f'DJANGO_ALLOWED_HOSTS={config["DJANGO_ALLOWED_HOSTS"]}\n')
            f.write('#AWS_ACCESS_KEY_ID= [NOT USED]\n')
            f.write('#AWS_SECRET_ACCESS_KEY= [NOT USED]\n\n')
            
            # PostgreSQL settings
            f.write('# PostgreSQL settings\n')
            f.write('# Live database\n')
            f.write(f'POSTGRES_USER={config["POSTGRES_USER"]}\n')
            f.write(f'POSTGRES_PASSWORD={config["POSTGRES_PASSWORD"]}\n')
            f.write(f'POSTGRES_DB={config["POSTGRES_DB"]}\n')
            f.write(f'DATABASE_URL={config["DATABASE_URL"]}\n\n')
            
            f.write('# Archive database\n')
            f.write(f'ARCHIVE_POSTGRES_USER={config["ARCHIVE_POSTGRES_USER"]}\n')
            f.write(f'ARCHIVE_POSTGRES_PASSWORD={config["ARCHIVE_POSTGRES_PASSWORD"]}\n')
            f.write(f'ARCHIVE_POSTGRES_DB={config["ARCHIVE_POSTGRES_DB"]}\n')
            f.write(f'ARCHIVE_DATABASE_URL={config["ARCHIVE_DATABASE_URL"]}\n\n')
            
            # Redis settings
            f.write('# Redis configuration\n')
            f.write(f'REDIS_PASSWORD={config["REDIS_PASSWORD"]}\n\n')
            
            # Additional settings
            f.write('# Additional settings\n')
            f.write(f'LOCALHOST_DOCKER={config["LOCALHOST_DOCKER"]}\n')
            f.write(f'DJANGO_DEBUG_TOOLBAR_ENABLED={config["DJANGO_DEBUG_TOOLBAR_ENABLED"]}\n')
            f.write(f'USE_REDIS_IN_DEV={config["USE_REDIS_IN_DEV"]}\n')
            f.write(f'RESTRICT_NEW_USERS={config["RESTRICT_NEW_USERS"]}\n')
        
        print(f"\n✅ Environment file created: {env_path}")
        
        # Show summary
        print(f"\n📋 Configuration Summary:")
        print(f"   Mode: {mode.title()}")
        print(f"   DEBUG: {config['DEBUG']}")
        print(f"   Database: {config['POSTGRES_DB']}")
        print(f"   Archive DB: {config['ARCHIVE_POSTGRES_DB']}")
        if use_random_admin:
            print(f"   Admin password: {config['ADMIN_PASSWORD']}")
        if use_random_db_pass:
            print(f"   DB password: {config['POSTGRES_PASSWORD']}")
            print(f"   Archive DB password: {config['ARCHIVE_POSTGRES_PASSWORD']}")
        if use_random_redis:
            print(f"   Redis password: {config['REDIS_PASSWORD']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = create_env_file()
    sys.exit(0 if success else 1)
