[Khan Academy](http://www.khanacademy.org/)'s core mission is to "provide a free world-class education for anyone anywhere", and as [70% of the world's population is without access to the internet](http://en.wikipedia.org/wiki/Global_Internet_usage), primarily in the developing world, providing an alternative delivery mechanism for Khan Academy content is key to fulfilling this mission.

KA Lite is a lightweight Django web app for serving core Khan Academy content (videos and exercises) from a local server, without needing internet connectivity. Primary use cases include:
* Mobile school "vans", which transport a server and multiple laptops/tablets between a number of schools (or orphanages, community centers, etc) in remote communities on a rotating basis, and syncing up with a central database (to download new content and upload analytics) when in an area with internet connectivity.
* For servers/computer labs located in remote schools, which could be slowly syncing with a central server over a cell/satellite network or via USB keys.
* In correctional facilities and other environments where providing educational materials is of value, but users cannot be given general internet access.

**Installing and Running**

First, clone the repository. As it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule, you will need to do a recursive clone, e.g.:
`git clone --recursive https://github.com/jamalex/ka-lite.git`

Then, you'll need to ensure you have Python installed (version >= 2.5 and < 3). On most versions of Linux (and on OSX), you should already have Python installed. Otherwise, you can [install Python 2.7 for Windows](http://www.python.org/download/releases/2.7.3/).

Then, from your shell/terminal/command line, _cd_ into the `./ka-lite/kalite/` directory and run:
`./manage.py syncdb`
to initialize the database, and to set an initial admin username/password.

After that, run:
`./manage.py migrate`
to update the database schema.

To run the server in development mode, simply run:
`./manage.py runserver`
and then visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.