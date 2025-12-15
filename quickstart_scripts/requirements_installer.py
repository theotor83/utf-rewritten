"""
Requirements installer module for Django project quickstart.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """
    Install requirements from requirements.txt file.
    
    Returns:
        bool: True if installation successful, False otherwise
    """
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Requirements file not found: {requirements_file}")
        return False
    
    print(f"Found requirements file: {requirements_file}")
    print("Installing Python packages...")
    
    try:
        # Run pip install
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True, check=True)
        
        if result.returncode == 0:
            print("[+] All requirements installed successfully!")
            return True
        else:
            print(f"Installation failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        return False

if __name__ == "__main__":
    success = install_requirements()
    sys.exit(0 if success else 1)
