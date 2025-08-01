"""
Server starter for Django project quickstart.
Handles starting the development server or Docker containers.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def get_user_choice():
    """Get user's choice for server quickstart method."""
    print("🚀 Server Quickstart Options")
    print("=" * 30)
    print("1. Django Development Server (python manage.py runserver)")
    print("2. Docker Compose (docker compose up)")
    
    while True:
        choice = input("\nSelect server quickstart method [1/2]: ").strip()
        if choice == "1":
            return "django"
        elif choice == "2":
            return "docker"
        else:
            print("Please enter 1 or 2.")

def check_docker_availability():
    """Check if Docker and Docker Compose are available."""
    try:
        # Check docker
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "Docker not found"
        
        # Check docker compose
        result = subprocess.run(["docker", "compose", "version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            # Try older docker-compose command
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False, "Docker Compose not found"
            return True, "docker-compose"
        
        return True, "docker compose"
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Docker not available"

def start_django_server():
    """Start Django development server."""
    project_dir = Path(__file__).parent.parent
    manage_py = project_dir / "manage.py"
    
    if not manage_py.exists():
        print(f"❌ manage.py not found in {project_dir}")
        return False
    
    print("🔥 Starting Django development server...")
    print("📍 Server will be available at: http://127.0.0.1:8000/")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the Django development server
        subprocess.run([
            sys.executable, str(manage_py), "runserver"
        ], cwd=str(project_dir))
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to start Django server: {e}")
        return False

def start_docker_server():
    """Start Docker containers."""
    project_dir = Path(__file__).parent.parent
    compose_file = project_dir / "docker-compose.yml"
    
    if not compose_file.exists():
        print(f"❌ docker-compose.yml not found in {project_dir}")
        print("   Make sure you have a Docker Compose configuration file.")
        return False
    
    # Check Docker availability
    docker_available, compose_command = check_docker_availability()
    if not docker_available:
        print(f"❌ {compose_command}")
        print("   Please install Docker and Docker Compose to use this option.")
        return False
    
    print("🐳 Starting Docker containers...")
    print("⏹️  Use Ctrl+C to stop, or run 'docker compose down' to stop containers")
    
    try:
        # Stop existing containers
        print("🛑 Stopping existing containers...")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "down"], 
                         cwd=str(project_dir), timeout=30)
        else:
            subprocess.run(["docker-compose", "down"], 
                         cwd=str(project_dir), timeout=30)
        
        # Start containers with build
        print("🔨 Building and starting containers...")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "up", "-d", "--build"], 
                         cwd=str(project_dir), check=True)
        else:
            subprocess.run(["docker-compose", "up", "-d", "--build"], 
                         cwd=str(project_dir), check=True)
        
        print("✅ Docker containers started successfully!")
        print("📍 Check your docker-compose.yml for port mappings")
        
        # Show container status
        print("\n📊 Container Status:")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "ps"], cwd=str(project_dir))
        else:
            subprocess.run(["docker-compose", "ps"], cwd=str(project_dir))
        
        # Follow logs
        print("\n📝 Container logs (Press Ctrl+C to stop following logs):")
        print("-" * 50)
        try:
            if "docker compose" in compose_command:
                subprocess.run(["docker", "compose", "logs", "-f"], cwd=str(project_dir))
            else:
                subprocess.run(["docker-compose", "logs", "-f"], cwd=str(project_dir))
        except KeyboardInterrupt:
            print("\n🛑 Stopped following logs (containers are still running)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker containers: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Docker quickstart interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error starting Docker: {e}")
        return False

def start_server():
    """
    Start the server based on user choice.
    
    Returns:
        bool: True if quickstart was successful, False otherwise
    """
    try:
        choice = get_user_choice()
        
        if choice == "django":
            return start_django_server()
        elif choice == "docker":
            return start_docker_server()
        else:
            print("❌ Invalid choice")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Server quickstart cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error during server quickstart: {e}")
        return False

if __name__ == "__main__":
    success = start_server()
    sys.exit(0 if success else 1)
