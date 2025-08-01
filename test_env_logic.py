#!/usr/bin/env python3
"""
Test script to verify the environment-based logic in migration runner and server starter.
"""

import sys
import os
from pathlib import Path

# Add quickstart_scripts to path
script_dir = Path(__file__).parent
quickstart_dir = script_dir / "quickstart_scripts"
sys.path.insert(0, str(quickstart_dir))

def create_test_env(development_mode, localhost_docker):
    """Create a test .env file with specific settings."""
    env_path = Path(__file__).parent / ".env.test"
    with open(env_path, 'w') as f:
        f.write(f'DEVELOPMENT_MODE={development_mode}\n')
        f.write(f'LOCALHOST_DOCKER={localhost_docker}\n')
        f.write('SECRET_KEY=test-key\n')
    return env_path

def test_migration_logic():
    """Test migration runner logic."""
    from migration_runner import read_env_variable, is_development_mode
    
    tests = [
        ("True", True, "Development mode should run migrations"),
        ("False", False, "Production mode should skip migrations"),
        ("true", True, "Case insensitive True should work"),
        ("false", False, "Case insensitive False should work"),
    ]
    
    print("🗃️  Testing Migration Runner Logic")
    print("=" * 40)
    
    for dev_mode, expected, description in tests:
        # Create temporary .env file
        env_path = create_test_env(dev_mode, "True")
        
        # Temporarily modify the function to use test file
        original_env_path = Path(__file__).parent / ".env"
        test_env_path = Path(__file__).parent / ".env.test"
        
        # Backup original if exists
        backup_needed = original_env_path.exists()
        if backup_needed:
            original_env_path.rename(Path(__file__).parent / ".env.backup")
        
        # Use test file
        test_env_path.rename(original_env_path)
        
        try:
            result = is_development_mode()
            status = "✅" if result == expected else "❌"
            print(f"  {status} {description}: {result} (expected {expected})")
        finally:
            # Restore original
            original_env_path.rename(test_env_path)
            if backup_needed:
                (Path(__file__).parent / ".env.backup").rename(original_env_path)
            
            # Clean up test file
            if test_env_path.exists():
                test_env_path.unlink()

def test_server_logic():
    """Test server starter logic."""
    from server_starter import is_development_mode, is_localhost_docker
    
    test_scenarios = [
        ("False", "False", "Production: Always Docker"),
        ("True", "False", "Dev + No Docker: Always runserver"),
        ("True", "True", "Dev + Docker: User choice"),
    ]
    
    print("\n🚀 Testing Server Starter Logic")
    print("=" * 40)
    
    for dev_mode, docker_mode, description in test_scenarios:
        # Create temporary .env file
        env_path = create_test_env(dev_mode, docker_mode)
        
        # Temporarily modify the function to use test file
        original_env_path = Path(__file__).parent / ".env"
        test_env_path = Path(__file__).parent / ".env.test"
        
        # Backup original if exists
        backup_needed = original_env_path.exists()
        if backup_needed:
            original_env_path.rename(Path(__file__).parent / ".env.backup")
        
        # Use test file
        test_env_path.rename(original_env_path)
        
        try:
            dev_result = is_development_mode()
            docker_result = is_localhost_docker()
            
            expected_dev = dev_mode.lower() == "true"
            expected_docker = docker_mode.lower() == "true"
            
            dev_ok = dev_result == expected_dev
            docker_ok = docker_result == expected_docker
            
            status = "✅" if (dev_ok and docker_ok) else "❌"
            print(f"  {status} {description}")
            print(f"      DEVELOPMENT_MODE: {dev_result} (expected {expected_dev})")
            print(f"      LOCALHOST_DOCKER: {docker_result} (expected {expected_docker})")
            
        finally:
            # Restore original
            original_env_path.rename(test_env_path)
            if backup_needed:
                (Path(__file__).parent / ".env.backup").rename(original_env_path)
            
            # Clean up test file
            if test_env_path.exists():
                test_env_path.unlink()

def main():
    """Run all tests."""
    print("🧪 Testing Environment-Based Logic")
    print("=" * 50)
    
    test_migration_logic()
    test_server_logic()
    
    print("\n📊 Logic Testing Complete!")
    print("   The scripts should now behave according to .env configuration")

if __name__ == "__main__":
    main()
