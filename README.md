[Khan Academy](http://www.khanacademy.org/)'s core mission is to "provide a free world-class education for anyone anywhere", and with 70% of the world's population not having access to the internet, providing an alternative delivery mechanism for Khan Academy content is key to fulfilling this mission.

Khan Academy Lite is a lightweight Django web app for hosting core Khan Academy content (videos and exercises) from a local server, without needing internet connectivity. Primary use cases include:
* Mobile school "vans", which transport a server and multiple laptops/tablets between a number of schools/orphanages in remote communities on a rotating basis, and syncing up with a central database (to download new content and upload analytics) when in an area with internet connectivity.
* For servers/computer labs located in remote schools, which could be slowly syncing with a central server over a cell network or via USB keys.

**Installing and Running**

First, clone the repository. As it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule, you will need to do a recursive clone, e.g.:
`git clone --recursive https://github.com/jamalex/ka-lite.git`

Then, you'll need to ensure you have Python installed (version >= 2.5 and < 3), and the following Python packages:
`django`, `django_annoying`, `django_extensions`, `M2Crypto`, `south`, and `requests` (using, for example, `easy_install` or `pip`)

(Note: the easiest way to install `M2Crypto` on Ubuntu is `sudo apt-get install python-m2crypto`)

Then, navigate into the `./ka-lite/kalite/` directory and run:
`./manage.py syncdb`
to initialize the database, and to set an admin username/password.

To run the server in development mode, simply run:
`./manage.py runserver`
