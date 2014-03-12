KA Lite is a medium-size project, so keeping a well-defined structure is essential to making it understandable.

Below is an outline of the directory structure for the project, as well as how apps are currently structured.


## Directories
The KA Lite project has the following subdirectories:

### Code
* [kalite](https://github.com/learningequality/ka-lite/tree/master/kalite) - Django apps we've created or downloaded and modified for the ka lite projects
* [python-packages](https://github.com/learningequality/ka-lite/tree/master/python-packages) - Django apps and Python package dependencies for apps within `kalite`
* [scripts](https://github.com/learningequality/ka-lite/tree/master/scripts) - OS-specific scripts for starting/stopping server (and other similar tasks)

### Resources
* [content](https://github.com/learningequality/ka-lite/tree/master/content) - contains video files and video preview images
* [data](https://github.com/learningequality/ka-lite/tree/develop/data) - private json data files the server uses
* [docs](https://github.com/learningequality/ka-lite/tree/master/docs) - .md files for developers and KA Lite users
* [locale](https://github.com/learningequality/ka-lite/tree/master/locale) - contains translations that are downloaded via language pack updates

## Apps

### KA Lite created / modified apps

Distributed server-specific - only used on the installable KA Lite server
* chronograph - Like UNIX `cron`: runs jobs (Django management commands), keeps logs
* config - generic app for setting server config options in the database
* django_cherrypy_wsgiserver - wrapper around cherrypy for use in Django
* khanload - code and commands for downloading Khan Academy's topic tree and user data
* updates - sister app of chronograph; updates job status from back-end management commands to the front-end UI

Shared - Shared between both technologies
* coachreports - graphical displays of student progress
* control_panel - summaries of all data (usage and syncing) 
* i18n - tools for implementing language packs, including interface translations, subtitles, and dubbed videos
* main - main website and student progress recording
* securesync - engine for syncing data, as well as defining users
* tests - framework for functional and performance testing
* utils - app-independent utilities (could be shared with the world!)

Central server-specific - only used on our online website and central data repository
* central - main KA Lite website
* contact - contact form
* faq - FAQ page
* registration - user registration and sign-in
* stats - summaries of data shared centrally.

### Library apps

These are located in the `python-packages` directory.

True libraries - usually get via `sudo apt-get`, but we download and ship for offline completeness
* cherrypy
* collections
* django
* httplib2
* pytz
* requests
* rsa
* selenium
* south

External helpers - Collected from around the web, we use this code without modification.
** NOTE **: many of these may belong to "true libraries" above.
* annoying
* dateutil
* debug_toolbar
* decorator
* django_extensions
* django_snippets
* git
* ifcfg
* iso8601
* khanacademy
* memory_profiler
* mplayer
* oauth
* pbkdf2
* polib
* postmark
* pyasn1
* werkzeug

Internal helpers - Other projects we authored, but that is used without modification here.
* playground


	
## App file structure

### Files
* Each app contains relevant standard Django files (`forms.py`, `models.py`, `views.py`, `urls.py`)
* Some apps have both HTML views as well as API/JSON views.  These are defined by `api_xxx.py` files, such as `api_views.py`, `api_urls.py`, etc.
* Any shared functions across the app/module with other apps should be defined within the `__init__.py` file
* Some apps have additional functionality, especially for central server - distributed server interactions (e.g. `api_client.py`).  This may get refactored...
