"""
Server starter for Django project quickstart.
Handles starting the development server or Docker containers based on .env configuration.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def read_env_variable(key, default=""):
    """Read a variable from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return default
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line[len(key)+1:]
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    return value
    except Exception:
        pass
    
    return default

def is_development_mode():
    """Check if we're in development mode based on .env file."""
    development_mode = read_env_variable("DEVELOPMENT_MODE", "False")
    return development_mode.lower() in ("true", "1", "yes", "on")

def is_localhost_docker():
    """Check if localhost Docker is enabled based on .env file."""
    localhost_docker = read_env_variable("LOCALHOST_DOCKER", "False")
    return localhost_docker.lower() in ("true", "1", "yes", "on")

def get_user_choice():
    """Get user's choice for server startup method."""
    print("Server Startup Options")
    print("=" * 30)
    print("1. Daphne ASGI Server (python -m daphne utf.asgi:application)")
    print("2. Docker Compose (docker compose up)")
    
    while True:
        choice = input("\nSelect server startup method [1/2]: ").strip()
        if choice == "1":
            return "daphne"
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

def start_daphne_server():
    """Start Daphne ASGI development server."""
    project_dir = Path(__file__).parent.parent
    manage_py = project_dir / "manage.py"
    
    if not manage_py.exists():
        print(f"manage.py not found in {project_dir}")
        return False
    
    print("Starting Daphne ASGI development server...")
    print("Server will be available at: http://127.0.0.1:8000/")
    print(" Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start Daphne with auto-reload for development convenience
        subprocess.run([
            sys.executable,
            "-m",
            "daphne",
            "-b",
            "127.0.0.1",
            "-p",
            "8000",
            "--proxy-headers",
            "--verbosity",
            "2",
            "--reload",
            "utf.asgi:application",
        ], cwd=str(project_dir))
        return True
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return True
    except Exception as e:
        print(f"Failed to start Daphne server: {e}")
        return False

def start_docker_server():
    """Start Docker containers."""
    project_dir = Path(__file__).parent.parent
    compose_file = project_dir / "docker-compose.yml"
    
    if not compose_file.exists():
        print(f"docker-compose.yml not found in {project_dir}")
        print("   Make sure you have a Docker Compose configuration file.")
        return False
    
    # Check Docker availability
    docker_available, compose_command = check_docker_availability()
    if not docker_available:
        print(f"{compose_command}")
        print("   Please install Docker and Docker Compose to use this option.")
        return False
    
    print("Starting Docker containers...")
    print(" Use Ctrl+C to stop, or run 'docker compose down' to stop containers")
    
    try:
        # Stop existing containers
        print("Stopping existing containers...")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "down"], 
                         cwd=str(project_dir), timeout=30)
        else:
            subprocess.run(["docker-compose", "down"], 
                         cwd=str(project_dir), timeout=30)
        
        # Start containers with build
        print("Building and starting containers...")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "up", "-d", "--build"], 
                         cwd=str(project_dir), check=True)
        else:
            subprocess.run(["docker-compose", "up", "-d", "--build"], 
                         cwd=str(project_dir), check=True)
        
        print("[+] Docker containers started successfully!")
        print("Check your docker-compose.yml for port mappings")
        
        # Show container status
        print("\nContainer Status:")
        if "docker compose" in compose_command:
            subprocess.run(["docker", "compose", "ps"], cwd=str(project_dir))
        else:
            subprocess.run(["docker-compose", "ps"], cwd=str(project_dir))
        
        # Follow logs
        print("\nContainer logs (Press Ctrl+C to stop following logs):")
        print("-" * 50)
        try:
            if "docker compose" in compose_command:
                subprocess.run(["docker", "compose", "logs", "-f"], cwd=str(project_dir))
            else:
                subprocess.run(["docker-compose", "logs", "-f"], cwd=str(project_dir))
        except KeyboardInterrupt:
            print("\nStopped following logs (containers are still running)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Docker containers: {e}")
        return False
    except KeyboardInterrupt:
        print("\nDocker startup interrupted by user")
        return False
    except Exception as e:
        print(f"Unexpected error starting Docker: {e}")
        return False

def start_server():
    """
    Start the server based on .env configuration and user choice.
    
    Logic:
    - If DEVELOPMENT_MODE=False (production): Always use Docker (no choice)
    - If DEVELOPMENT_MODE=True:
    - If LOCALHOST_DOCKER=True: Ask user to choose between Daphne or Docker
    - If LOCALHOST_DOCKER=False: Always use Daphne (no choice)
    
    Returns:
        bool: True if startup was successful, False otherwise
    """
    try:
        # Read environment configuration
        development_mode = is_development_mode()
        localhost_docker = is_localhost_docker()
        
        print("Server Startup")
        print("=" * 20)
        print(f"Development Mode: {development_mode}")
        print(f"Localhost Docker: {localhost_docker}")
        print()
        
        if not development_mode:
            # Production mode: Always use Docker
            print("Production mode detected (DEVELOPMENT_MODE=False)")
            print("Starting Docker containers (production deployment)...")
            return start_docker_server()
        else:
            # Development mode
            print("Development mode detected (DEVELOPMENT_MODE=True)")
            
            if localhost_docker:
                # Ask user to choose between Daphne and Docker
                print("Both Daphne and Docker are available")
                choice = get_user_choice()
                
                if choice == "daphne":
                    return start_daphne_server()
                elif choice == "docker":
                    return start_docker_server()
                else:
                    print("Invalid choice")
                    return False
            else:
                # Only use Daphne
                print("Starting Daphne ASGI development server (LOCALHOST_DOCKER=False)...")
                return start_daphne_server()
            
    except KeyboardInterrupt:
        print("\nServer startup cancelled by user")
        return False
    except Exception as e:
        print(f"Error during server startup: {e}")
        return False

if __name__ == "__main__":
    success = start_server()
    sys.exit(0 if success else 1)
