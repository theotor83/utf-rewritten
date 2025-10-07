# UTF-Rewritten 

> A modern Django-based revival of the Undertale France forum, preserving its original content and classic look forever.

<p align="center">
    <img src="./docs/images/utf-logo-crop.png" alt="UTF-Rewritten Logo" width="400" />
</p>

[![Django](https://img.shields.io/badge/Django-5.1.6-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

## 📋 Table of Contents

- [🗺️ Overview](#️-overview)
- [👉 Getting Started](#-getting-started)
- [🚀 Quickstart](#-quickstart)
- [🛠️ Manual Installation](#️-manual-installation)
- [🔧 Configuration](#-configuration)
- [📦 Populate Archive Database](#-populate-archive-database)
- [🐳 Docker Deployment](#-docker-deployment)
- [🔌 URLs Reference](#-urls-reference)
- [📚 Documentation](#-documentation)
- [📁 Project Structure](#-project-structure)
- [🤝 Contributing](#-contributing)
- [📝 TODO](#-todo)
- [📜 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)


## 🗺️ Overview

### What is this about?
UTF-Rewritten is a modern Django-based revival of Undertale France, an old french forum that was hosted by Xooit and ran on phpBB. The forum hoster shut down the original site around late 2024 and I wanted to preserve the experience, as well as the content of the forum.

### What are the main features?
This project scope increased as time went on, and now includes:
- Most of the phpBB features, such as basic forum features, polls, and private messaging
- The archive database
- A theme switcher, with a new design made by Xooit
- A 'Flashback' feature on the archive, allowing users to see the forum's simulated state in a past date
- A quickstart script, to easily set up the project

### Why was it created?
I was part of the community when I was very young, and still have some online friends from this forum. As the original site is no longer accessible, I wanted to recreate the original feeling of the forum, as well as its content. I also plan on becoming a backend developer, and this project serves as a valuable learning experience, with even more features than I first expected.

### How was the original content preserved?
The forum hoster didn't announce the shutdown in advance, but they had financial difficulties. In May 2024, I ran a web scraper to collect and archive as much content as possible from the forum before it was taken down. The forum was taken down months later but it was already long inactive, so 99.9% of the content was preserved. This includes around 2,000 users, 30,000 posts and 1,500 topics. The content from the original forum was exported to JSON files, and were then migrated again on a separate database meant to be read-only using scripts (available at `./archive/scripts`).

### Where can I see this project live?
The project has been deployed, and is currently live at [https://utf-rewritten.org/](https://utf-rewritten.org/).

### How is the website structured?

The application consists of two main Django apps:

1. **Forum App** (`/`): The main interactive forum where users can create topics, post replies, and engage in discussions
2. **Archive App** (`archive/`): A read-only interface to historical forum data stored in a separate database
<!-- TODO: Add a website architecture diagram -->

### What does the website look like?

Here is the index for the two themes:
<p align="center">
    <img src="./docs/images/utf-index-modern.png" alt="Screenshot of the archive's index, with the modern theme" width="800" />
    <br><em>Archive index with Modern theme</em>
</p>

<p align="center">
    <img src="./docs/images/utf-index.png" alt="Screenshot of the archive's index, with the classic theme" width="800" />
    <br><em>Archive index with Classic theme (phpBB like)</em>
</p>
<!-- TODO: Add more screenshots -->

## 👉 Getting Started

### Prerequisites

- Install Python 3.8+ **(3.10 recommended)**

If you plan to deploy UTF-Rewritten in a production environment, you will also need to install Docker.

### Setup Instructions

#### Windows:

```powershell
# Clone and setup virtual environment
git clone https://github.com/theotor83/utf-rewritten.git
cd utf-rewritten
python -m venv utf-rewritten.venv
utf-rewritten.venv\Scripts\Activate.ps1
```

#### Linux:
```bash
# Clone and setup virtual environment
git clone https://github.com/theotor83/utf-rewritten.git
cd utf-rewritten
python -m venv utf-rewritten.venv
source utf-rewritten.venv/bin/activate
```

After that, you are ready to run the quickstart script or follow the manual installation steps below.

> 💡 The quickstart script handles dependency installation, database setup, and admin user creation automatically. See more [here](#-quickstart).

### Project Highlights

| 📈 **Metric** | 🔢 **Value** | 
|---------------|--------------|
| **Archive Stats** | ~30,000 preserved posts, ~2,000 preserved users|
| **Technology Stack** | Django 5.1+ • PostgreSQL (SQLite in development) • Redis • Docker |
| **BBCode Tags** | 20+ supported formatting tags |
| **Setup Time** | < 5 minutes with quickstart script, up to 15 minutes for archive population |
| **Production Ready** | Full Docker deployment |

### Key Features

- **Historical Archive**: Access to ~30,000 preserved posts from the original Undertale France forum
- **Authentic phpBB Design**: Recreation of the classic forum aesthetic
- **Modern Backend**: Django 5.1+ with PostgreSQL, Redis caching, and Docker deployment
- **Full Forum Functionality**: Topics, posts, categories, user profiles, and private messaging
- **Rich BBCode Support**: 20+ BBCode tags including YouTube embeds, spoilers, and custom formatting
- **Advanced Search**: Comprehensive search across topics, posts, and users
- **Production Ready**: Complete Docker setup with Nginx, PostgreSQL, and Redis
- **One-Command Setup**: Automated installation script for instant deployment


## 🚀 Quickstart

### Prerequisites

- Python 3.8+ **(3.10 recommended)**

If you plan to deploy UTF-Rewritten in a production environment, you will also need to install Docker.

### 1. Clone the Repository

```bash
git clone https://github.com/theotor83/utf-rewritten.git
cd utf-rewritten
```

### 2. Create Virtual Environment

```bash
python -m venv utf-rewritten.venv
source utf-rewritten.venv/bin/activate  # On Windows: utf-rewritten.venv\Scripts\Activate.ps1
```

### 3. Run Quickstart Script

```bash
python quickstart.py
```

### 4. Follow the Script

Example output of the script:

```bash
$ python quickstart.py
✅ Virtual environment detected!
📦 Installing requirements...
⚙️ Setting up environment configuration...

📍 Deployment Mode Selection:
1. Development (local machine)
2. Production (remote server)
Select mode [1/2]: 1

⚙️ Configuration Mode:
1. Simple (recommended settings with minimal input)
2. Advanced (full customization)
Select configuration mode [1/2]: 1

✅ Generated Django secret key
✅ Applied development defaults
Generate random admin password [Y/n]: y
✅ Generated random admin password
...
```

If you want to simply run the project locally on `127.0.0.1:8000`, always choose 1 and yes. This will initialize the databases and default admin user with random passwords.

### 5. Start the ASGI Server

You can now launch the project with an ASGI server such as Daphne (already included in `requirements.txt`). This provides production-parity for WebSocket and long-lived connections while still working great for traditional HTTP requests.

```powershell
# Windows PowerShell
daphne -b 127.0.0.1 -p 8000 utf.asgi:application
```

```bash
# macOS / Linux
daphne -b 127.0.0.1 -p 8000 utf.asgi:application
```

Once running, visit [http://127.0.0.1:8000](http://127.0.0.1:8000) as you would with the regular development server.

### 6. Log In

If you want to log into your account, go to `http://127.0.0.1:8000/admin` with the username "Admin" and the password written on your `.env` file.

## 🛠️ Manual Installation

### Prerequisites

- Python 3.8+ **(3.10 recommended)**

If you plan to deploy UTF-Rewritten in a production environment, you will also need to install Docker.

### 1. Clone the Repository

```bash
git clone https://github.com/theotor83/utf-rewritten.git
cd utf-rewritten
```

### 2. Create Virtual Environment

```bash
python -m venv utf-rewritten.venv
source utf-rewritten.venv/bin/activate  # On Windows: utf-rewritten.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp env.example .env  # On Windows: copy env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here
DEVELOPMENT_MODE=True

# PostgreSQL Settings (Production)
POSTGRES_DB=utf_forum
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
DATABASE_URL=postgres://user:password@localhost:5432/utf_forum

# Archive Database
ARCHIVE_POSTGRES_DB=utf_archive
ARCHIVE_POSTGRES_USER=your_archive_user
ARCHIVE_POSTGRES_PASSWORD=your_archive_password
ARCHIVE_DATABASE_URL=postgres://user:password@localhost:5432/utf_archive

# Redis Configuration
USE_REDIS_IN_DEV=False
REDIS_PASSWORD=your_redis_password
REDIS_URL=redis://:password@localhost:6379/0

# Security
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1:8000
```

### 5. Database Setup

```bash
# Run migrations for main database
python manage.py migrate

# Run migrations for archive database
python manage.py migrate --database=archive

# Create superuser
python manage.py createsuperuser
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Start the ASGI Server

Use Daphne to serve the project over ASGI in development or staging environments:

```powershell
# Windows PowerShell
daphne -b 127.0.0.1 -p 8000 utf.asgi:application
```

```bash
# macOS / Linux
daphne -b 127.0.0.1 -p 8000 utf.asgi:application
```

If you prefer `python -m daphne`, replace `daphne` in the command above with `python -m daphne`.

## 🔧 Configuration

### Initial Setup

After running the migration files, your database is already populated with default categories and subforums. You can access the admin panel to create additional categories and customize your forum:

1. **Access Admin Panel**: Visit `http://127.0.0.1:8000/admin/`
2. **Create Categories**: Set up more forum categories and subforums
3. **Configure User Groups**: Set up user permissions and groups
4. **Create Smileys**: Add custom smileys for BBCode support

### Database Configuration

The application supports dual database configuration:

- **Default Database**: Main forum database for active content
- **Archive Database**: Read-only historical content

### Caching Configuration

- **Development**: Uses dummy cache by default, optional Redis
- **Production**: Redis cache with authentication support

### Media and Static Files

- Static files served from `static/` directory
- Media files (user uploads) stored in `media/` directory

## 📦 Populate Archive Database

### Development Server
To populate the archive database with historical content, run the following command:

```bash
python archive/scripts/populate_archive.py
```
This script will take a while to run, as there are almost 30,000 posts to import. It will copy all the data from the JSON files to the archive database. If you get an error about the models not being deleted, you can run the following command to delete the database and start over:

```bash
rm archive.sqlite3 # or whatever your archive database is named
python manage.py makemigrations
python manage.py migrate --database=archive
# Now, run the populate script again
python archive/scripts/populate_archive.py
```

### Dockerized Server

The same steps apply, but you need to run another script inside the Docker container:

```bash
docker-compose exec web python archive/scripts/populate_archive_docker.py
```

Note that this script is renamed to `populate_archive_docker.py` to avoid confusion with the local script. It will also take a while to run, as it will import all the data from the JSON files to the archive database.


## 🐳 Docker Deployment

### Development with Docker

```bash
# Clone and navigate to project
git clone https://github.com/theotor83/utf-rewritten.git
cd utf-rewritten

# Copy environment file
cp env.example .env  # On Windows: copy env.example .env

# Build and start services
docker-compose up --build

# Run migrations (in separate terminal)
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py migrate --database=archive
```

### Production Deployment

1. **Configure environment variables** in `.env`
2. **Set up SSL certificates** in `docker/nginx/ssl/`
3. **Configure domain settings** in nginx configuration
4. **Deploy with docker-compose**:

```bash
docker-compose -f docker-compose.yml up -d
```

### Docker Services

- **web**: Django application server
- **db**: PostgreSQL main database
- **archive_db**: PostgreSQL archive database
- **redis**: Redis cache server
- **nginx**: Reverse proxy and static file server

<!-- TODO: Add this: ![Docker Architecture](./docs/images/docker-architecture.png) -->


## 🔌 URLs Reference

### Forum URLs (for logged-out users)

| URL | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirects to index |
| `/index/` | GET | Forum homepage |
| `/f<id>-<slug>/` | GET | View topics inside subforum |
| `/t<id>-<slug>/` | GET | View posts inside topic |
| `/c<id>-<slug>/` | GET | View topics inside category |
| `/profile/<id>/` | GET | User profile page |
| `/memberlist/` | GET | Members overview page |
| `/groups/` | GET | Groups overview page |
| `/groups/g<id>` | GET | Group details page |
| `/search/` | GET/POST | Search topics and posts |
| `/search_results/` | GET | Search results |
| `/login/` | GET/POST | User login |
| `/register/` | GET/POST | User registration |
| `/p/<id>` | GET | Post redirect |

### Logged-in exclusive URLs

| URL | Method | Description |
|----------|--------|-------------|
| `/new_topic/?f=<id>` | GET/POST | New topic creation page |
| `/new_post/?t=<id>` | GET/POST | New post creation page |
| `/edit_post/<id>` | GET/POST | Edit post page |
| `/edit_profile/` | GET/POST | Edit profile page |
| `/pm_inbox/` | GET | Private messages inbox |
| `/new_pm_thread/` | GET/POST | New private message thread |
| `/new_pm/<id>/` | GET/POST | New private message |
| `/logout/` | GET/POST | User logout |

### Archive URLs

The archive URLs are read-only and do not require authentication. They can be accessed by adding `/archive/` to the start of the main URLs.

### Admin URLs

| URL | Method | Description |
|----------|--------|-------------|
| `/admin/` | GET | Django admin interface |
| `/admin/forum/` | GET | Forum administration |
| `/admin/archive/` | GET | Archive administration |

## 📚 Documentation

### Forum Models Schema

<p align="center">
    <img src="./docs/images/db-schema.png" alt="Database Schema" width="600" />
</p>

#### Archive Models

Similar to Forum models but read-only, used for historical content preservation. Uses FakeUser model to replace the auth_user, and does not include PrivateMessage or PrivateMessageThread models.

### BBCode Support

The application uses `precise_bbcode` for rich text formatting:

- **Supported Tags**: `[b]`, `[i]`, `[u]`, `[s]`, `[url]`, `[img]`, `[quote]`, `[code]`, `[color]`, `[size]`, `[youtube]`, `[font]`, `[pxsize]`, `[spoiler]`, `[marquee]`, `[justify]`, `[rawtext]`, `[hr]`, `[yt]`
- **Custom Tags**: More tags can be added in `forum/bbcode_tags.py`
- **Security**: XSS protection and content sanitization

### Custom Theme Processing

UTF-Rewritten supports custom theme development and processing through the following theming system:

#### Theme Selection Logic

- Themes are selected based on the user's `theme` cookie
- Themes are registered in the `THEME_LIST` setting, which is a list of theme names
- The default theme is determined by the `DEFAULT_THEME` setting in `settings.py`
    - If not set, it defaults to the first theme in `THEME_LIST`
- If the user's theme is not found in `THEME_LIST`, or the cookie is not present, the default theme is used

#### Theme Structure

```
templates/
└── 📁 themes/
    └── 📁 theme_1/           
        ├── base.html          # Custom base template for theme 1
        ├── index.html         # Custom index template for theme 1
        └── login.html         # Custom login template for theme 1
    └── 📁 theme_2/           
        ├── base.html          # Custom base template for theme 2
        ├── index.html         # Custom index template for theme 2
        └── login.html         # Custom login template for theme 2
    └── 📁 theme_3/           
        ├── base.html          # Custom base template for theme 3
        ├── index.html         # Custom index template for theme 3
        └── login.html         # Custom login template for theme 3
```

#### Creating Custom Themes

1. **Theme Registration**: Register theme in Django settings, inside the `THEME_LIST` variable.
2. **Theme Directory**: Create new theme directory in `templates/themes/`, with the same name as the theme registered in `THEME_LIST`.
   - Example: `templates/themes/dark/`, with `THEME_LIST = [..., 'dark']` in `settings.py`.
3. **Templates**: Copy and paste default theme templates, then customize. The names must be the same as the default templates, so that they can be overridden.
4. **Static Assets**: Create a new directory in `static/` for theme-specific CSS, JS, and images, following this naming convention:
   - Example: `static/_theme_[themename]/css/`, `static/_theme_[themename]/js/`, `static/_theme_[themename]/images/`...
5. **Additional Context**: Add any additional context needed for the theme in `forum/views_context_processors.py`, in `THEME_CONTEXT_REGISTRY`.

#### Theme Processing Pipeline

- **Custom Render Function**: The views use the `theme_render` function to load templates based on the active theme, which is selected according to the user's `theme` cookie.
- **Context Processing**: The context is processed through `THEME_CONTEXT_REGISTRY`, which allows themes to add custom data to the context.

#### Built-in Themes

- **Classic phpBB** : Faithful recreation of original Undertale France design
- **Modern** (default): The current, responsive theme of Xooit, that was introduced in 2024

<!-- TODO: Add theme screenshots and customization examples -->

## 📁 Project Structure

```
utf-rewritten/
│
├── 📁 archive/                 # Archive app (read-only historical content)
│   ├── models.py               # Archive-specific models
│   ├── views.py                # Archive viewing logic
│   ├── templates/              # Archive templates
│   └── 📁 scripts/             # Archive-related scripts
│       └── populate_archive.py # Populate archive database script
│
├── 📁 forum/               # Main forum application
│   ├── models.py           # Forum models (User, Topic, Post, etc.)
│   ├── views.py            # Forum views and logic
│   ├── forms.py            # Django forms
│   ├── middleware.py       # Custom middleware
│   ├── templatetags/       # Custom template tags
│   └── management/         # Management commands
│
├── 📁 precise_bbcode/      # BBCode processing engine
│
├── 📁 quickstart_scripts/  # Automated setup scripts
│   ├── env_creator.py      # Environment setup
│   ├── migration_runner.py # Database migration handler
│   └── server_starter.py   # Development server launcher
│
├── 📁 templates/               # Django templates
│   ├── base.html               # Base template
│   ├── index.html              # Forum homepage
│   ├── topic_details.html      # Topic view
│   ├── subforum_details.html   # Subforum view
│   ├── category_details.html   # Category view
│   ├── ...
│   └── includes/               # Template partials
│
├── 📁 static/              # Static files (CSS, JS, images)
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   └── images/             # Static images
│
├── 📁 media/               # User-uploaded content
│   ├── images/             # User images
│   └── archive/            # Archive media files
│
├── 📁 docker/              # Docker configuration
│   ├── nginx/              # Nginx configuration
│   └── redis/              # Redis configuration
│
├── 📁 utf/                 # Django project settings
│   ├── settings.py         # Main settings file
│   ├── urls.py             # URL routing
│   ├── routers.py          # Database routing
│   └── wsgi.py             # WSGI configuration
│
├── 🐳 docker-compose.yml   # Docker Compose configuration
├── 🐳 Dockerfile          # Docker image definition
├── 📋 requirements.txt     # Python dependencies
├── ⚙️ manage.py            # Django management script
├── 🚀 quickstart.py        # Automated setup script
└── 📖 README.md            # This file
```

## 🤝 Contributing

### Reporting Issues

Please use the [GitHub Issues](https://github.com/theotor83/utf-rewritten/issues) page to report bugs or request features.

## 📝 TODO

- [x] 🎨**Use a New Modern Theme**
- [ ] 📊 **Optimize Category View Performance**
- [ ] 🔌 **Create an API**
- [ ] 💬 **Implement Chatbox**
- [ ] 🔄 **Implement Moved Topics**
- [ ] 👥 **Add "Who's Online" Feature**
- [ ] ♻️ **Implement More Caching**
- [x] 📖 **Optimize Topic Read Status**
- [ ] ✉️ **Improve Private Messaging**
- [ ] 😊 **Populate Database with Prefilled Smileys**
- [x] 🏷️ **Populate Database with Prefilled Group Icons**
- [x] 🔗 **Make the "MP" Button Link To a Prefilled Form**
- [ ] ➕ **Make the "Plus" Toolbar Button Work**
- [x] ⏳ **Add Time Machine Pagination in Subforum View**
- [ ] 🧮 **Add Time Machine Approximate Views for Topics**
- [ ] ⏱️ **Annotate past_total_children in Time Machine Mode**
- [x] 🧹 **Replace Every Remnants of phpBB Links**
- [x] 🚫 **Show Login Forms Errors**
- [ ] 🐛 **Fix Archive Memberlist Username Ordering**
- [ ] 🐛 **Fix Weird Parser Behavior**
- [ ] 🐛 **Fix Spoiler Tag Animation**
- [ ] 🧾 **Improve This README**


## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Théo Torregrossa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Sariel**: For helping me with some frontend elements
- **Django Team**: For the amazing framework
- **Docker**: For making my life easier but also harder sometimes
- **precise_bbcode**: For making my life even easier
- **Maltangle**: For creating the original Undertale France forum

---

<div align="center">

**Made with ❤️ by [Théo Torregrossa](https://github.com/theotor83)**

<p align="center">
    <img src="./docs/images/dog.png" alt="UTF-Rewritten Footer" />
</p>

[⬆ Back to Top](#utf-rewritten-)

</div>


<!-- ![Admin Interface](./docs/images/admin-interface.png) -->
