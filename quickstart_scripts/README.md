# Django Project Quick Startup System

This startup system automates the complete setup process for the Django project, making it easy to get up and running quickly.

## Overview

The startup system consists of a main script (`startup.py`) and several sub-scripts in the `quickstart_scripts/` directory that handle different aspects of the setup process.

## Usage

Simply run the main startup script:

```bash
python startup.py
```

## What It Does

The startup script performs the following steps in order:

### 1. Virtual Environment Check
- Checks if you're running in a virtual environment
- Warns if not and asks for confirmation to continue

### 2. Requirements Installation
- Automatically installs all Python packages from `requirements.txt`
- Uses pip to ensure all dependencies are available

### 3. Environment Configuration
- Creates a `.env` file based on user preferences
- Supports two deployment modes:
  - **Development**: Local machine with debug settings
  - **Production**: Remote server with security settings
- Offers two configuration modes:
  - **Simple**: Recommended settings with minimal input
  - **Advanced**: Full customization of all settings

### 4. Database Migrations
- **Development Mode** (`DEVELOPMENT_MODE=True`): 
  - Runs `python manage.py makemigrations`
  - Applies migrations to the main database
  - Applies migrations to the archive database
- **Production Mode** (`DEVELOPMENT_MODE=False`): 
  - Skips migrations (handled within Docker containers)

### 5. Server Startup
Server startup behavior is automatically determined by environment configuration:

- **Production Mode** (`DEVELOPMENT_MODE=False`): 
  - Always starts Docker containers (no user choice)
  - Assumes production deployment with Docker
- **Development Mode** (`DEVELOPMENT_MODE=True`):
  - If `LOCALHOST_DOCKER=True`: User chooses between Django dev server or Docker
  - If `LOCALHOST_DOCKER=False`: Always starts Django dev server (no choice)

## Environment Configuration Features

### Security Features
- Generates secure random passwords for databases, Redis, and admin
- Creates a strong Django secret key
- Validates configuration for potential security issues

### Smart Defaults
In **Simple Mode**, the script applies logical defaults based on deployment mode:

**Development Mode:**
- `DEBUG=True`
- `DEVELOPMENT_MODE=True`
- `LOCALHOST_DOCKER=True`
- `DJANGO_DEBUG_TOOLBAR_ENABLED=True`
- `USE_REDIS_IN_DEV=False`

**Production Mode:**
- `DEBUG=False`
- `DEVELOPMENT_MODE=False`
- `LOCALHOST_DOCKER=False`
- `DJANGO_DEBUG_TOOLBAR_ENABLED=False`
- `USE_REDIS_IN_DEV=False`

### Configuration Validation
The system warns about potentially problematic configurations, such as:
- Having `DEBUG=True` in production mode
- Using development settings in production mode

### Backup Protection
- Automatically backs up existing `.env` files
- Creates numbered backups (`old.env`, `old(1).env`, etc.)
- Asks for confirmation before overwriting

## Sub-Scripts

### `requirements_installer.py`
- Installs packages from `requirements.txt`
- Provides detailed output and error handling

### `env_creator.py`
- Interactive environment file creation
- Password generation and validation
- Configuration mode selection
- Backup handling

### `migration_runner.py`
- Automatically detects deployment mode from `.env` file
- **Development mode**: Runs Django migrations for both databases
- **Production mode**: Skips migrations (handled by Docker)
- Handles both main and archive database migrations
- Shows migration status in development mode

### `server_starter.py`
- Automatically determines startup method based on `.env` configuration
- **Production mode**: Always starts Docker containers
- **Development mode**: 
  - With `LOCALHOST_DOCKER=True`: User chooses between Django dev server and Docker
  - With `LOCALHOST_DOCKER=False`: Always starts Django dev server
- Docker availability checking
- Container management and log following

## Error Handling

The system includes comprehensive error handling:
- Each step can fail gracefully without affecting others
- Clear error messages and suggestions
- Proper cleanup on interruption

## Requirements

- Python 3.6+
- pip (for package installation)
- Docker and Docker Compose (optional, for Docker startup mode)

## Files Generated

- `.env`: Environment configuration file
- `old.env` (or numbered variants): Backup of existing environment files

## Security Notes

- Generated passwords are cryptographically secure
- Database URLs use placeholder hosts that may need adjustment
- Review generated `.env` file before production use
- Keep `.env` file private and never commit to version control

## Troubleshooting

If the script fails at any step:

1. **Virtual Environment Issues**: Activate your virtual environment first
2. **Requirements Installation**: Check internet connection and pip version
3. **Environment Creation**: Ensure write permissions in project directory
4. **Migration Issues**: Check database connectivity and settings
5. **Server Startup**: Verify Docker installation for Docker mode

## Manual Steps After Setup

After running the startup script, you may need to:

1. Adjust database URLs in `.env` if using different hosts
2. Create a superuser: `python manage.py createsuperuser`
3. Collect static files for production: `python manage.py collectstatic`
4. Configure your web server (nginx, apache) for production deployment

## Example Run

```
================================================================================
Django Project Quick Startup Script
================================================================================

✅ Virtual environment detected!

📦 Installing requirements...
✅ Requirements installed successfully!

⚙️  Setting up environment configuration...
🔧 Environment Configuration Setup
========================================

⚠️  An existing .env file was found!
Do you want to backup the existing .env file? [Y/n]: y
✅ Existing .env backed up as old.env

📍 Deployment Mode Selection:
1. Development (local machine)
2. Production (remote server)
Select mode [1/2]: 1

🎯 Selected: Development mode

⚙️  Configuration Mode:
1. Simple (recommended settings with minimal input)
2. Advanced (full customization)
Select configuration mode [1/2]: 1

🔑 Basic Configuration:
✅ Generated Django secret key
✅ Applied development defaults

👤 Admin Configuration:
Generate random admin password [Y/n]: y
✅ Generated random admin password

🗄️  Database Configuration:
Note: Database URLs are required and must be configured manually
Generate random database passwords [Y/n]: y
✅ Generated random database passwords

📝 Using default database URL format with Docker service name 'db'
   You may need to adjust the host (db) depending on your setup

🔴 Redis Configuration:
Generate random Redis password [Y/n]: y
✅ Generated random Redis password

✅ Environment file created: c:\code\github\django\utf-rewritten\.env

📋 Configuration Summary:
   Mode: Development
   DEBUG: True
   Database: utf_forum
   Archive DB: utf_archive
   Admin password: kX9#mN2$pL8@vR4*qS7!
   DB password: aB3$nM8&yT5#xK2@
   Archive DB password: pQ7!rS4$mN9@vL2#
   Redis password: zX6*bC8&nM3!kL9@

✅ Environment file created successfully!

🗃️  Running database migrations...
🗃️  Database Migration Runner
===================================

📝 Creating migration files...
✅ Making migrations completed successfully!

🗄️  Applying migrations to main database...
✅ Migrating main database completed successfully!

📚 Applying migrations to archive database...
✅ Migrating archive database completed successfully!

✅ All database migrations completed successfully!

✅ Migrations completed successfully!

🚀 Starting server...
🚀 Server Startup Options
==============================
1. Django Development Server (python manage.py runserver)
2. Docker Compose (docker compose up)

Select server startup method [1/2]: 1

🔥 Starting Django development server...
📍 Server will be available at: http://127.0.0.1:8000/
⏹️  Press Ctrl+C to stop the server
--------------------------------------------------
```
