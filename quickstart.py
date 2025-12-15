#!/usr/bin/env python3
"""
Django Project Quickstart Script
===================================

This script automates the setup process for the Django project including:
1. Virtual environment check and requirements installation
2. Environment file creation with user preferences
3. Database migrations
4. Server start (Django dev server or Docker)

Usage: python quickstart.py
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

# Add the quickstart_scripts directory to the Python path
SCRIPT_DIR = Path(__file__).parent
QUICKSTART_DIR = SCRIPT_DIR / "quickstart_scripts"
sys.path.insert(0, str(QUICKSTART_DIR))

def check_virtual_env():
    """Check if we're running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_user_confirmation(message, default="n"):
    """Get user confirmation for yes/no questions."""
    valid = {"yes": True, "y": True, "no": False, "n": False}
    if default == "y":
        prompt = " [Y/n] "
    else:
        prompt = " [y/N] "
    
    while True:
        choice = input(message + prompt).lower().strip()
        if choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

def main():
    """Main quickstart script execution."""
    print("=" * 60)
    print("Django Project Quickstart Script")
    print("=" * 60)
    print()
    
    # Step 1: Check virtual environment
    if not check_virtual_env():
        print("[!] WARNING: You are not running in a virtual environment!")
        print("It's recommended to use a virtual environment to avoid conflicts.")
        print()
        if not get_user_confirmation("Do you want to continue anyway?"):
            print("Setup cancelled. Please activate your virtual environment and try again.")
            print("To create and activate a virtual environment:")
            print("  python -m venv venv")
            print("  venv\\Scripts\\activate  # On Windows")
            print("  source venv/bin/activate  # On Linux/Mac")
            return 1
    else:
        print("[+] Virtual environment detected!")
    
    print()
    
    # Step 2: Install requirements
    print("Installing requirements...")
    try:
        # Import the requirements installation script
        from requirements_installer import install_requirements
        if not install_requirements():
            print(" Failed to install requirements!")
            return 1
        print("[+] Requirements installed successfully!")
    except ImportError:
        print(" Could not import requirements installer!")
        return 1
    except Exception as e:
        print(f" Error installing requirements: {e}")
        return 1
    
    print()
    
    # Step 3: Create .env file
    print(" Setting up environment configuration...")
    try:
        from env_creator import create_env_file
        if not create_env_file():
            print(" Failed to create .env file!")
            return 1
        print("[+] Environment file created successfully!")
    except ImportError:
        print(" Could not import environment creator!")
        return 1
    except Exception as e:
        print(f" Error creating .env file: {e}")
        return 1
    
    print()
    
    # Step 4: Run migrations
    print(" Running database migrations...")
    try:
        from migration_runner import run_migrations
        if not run_migrations():
            print(" Failed to run migrations!")
            return 1
        print("[+] Migrations completed successfully!")
    except ImportError:
        print(" Could not import migration runner!")
        return 1
    except Exception as e:
        print(f" Error running migrations: {e}")
        return 1
    
    print()
    
    # Step 5: Start server
    print("Starting server...")
    try:
        from server_starter import start_server
        start_server()
    except ImportError:
        print(" Could not import server starter!")
        return 1
    except Exception as e:
        print(f" Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        sys.exit(1)
