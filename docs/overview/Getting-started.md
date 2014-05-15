Firstly, thank you for being willing to offer your time to contribute to the KA Lite efforts! The project is run by volunteers dedicated to helping make educational materials more accessible to those in need, and every contribution makes a difference. Feel free to follow the instructions below to start playing with the codebase, but you may want to [contact us](http://jamiealexandre.com/contact/) to figure out what would be good for you to work on, or take a look at the [GitHub issues page](https://github.com/learningequality/ka-lite/issues), and jump right in!

### Getting started

1. Fork the main KA Lite repository ([signing up and configuring a GitHub account](https://help.github.com/categories/54/articles) first, if needed).
2. Clone your own repository (the one you forked), e.g., if you're using SSH authentication, it would be:
`git clone --recursive git@github.com:YOURACCOUNTNAME/ka-lite.git` (you can copy this url from your repository page)
3. After cloning, switch to the `develop` branch, which is where any commits you make should go (unless you want to make a feature branch): `git checkout develop` (we are roughly following the [successful git branching model](http://nvie.com/posts/a-successful-git-branching-model/) conventions, though we haven't moved to using release and hotfix branches yet)
4. In the `ka-lite/kalite` directory, add a file called `local_settings.py`, and put `DEBUG = True` in it.
5. Run the `install.sh` (Linux/OSX) or `install.bat` script (in the `ka-lite` directory) to initialize the database. (Take a look inside the file to get a sense of what it's doing).
6. Open two terminal/shell windows, in the `ka-lite/kalite` directory. In one, run `python manage.py runserver` (to start the Django development server), and in the other, run `python manage.py cronserver 5` (to run the background processing script, which does things like download requested videos).
7. Load http://127.0.0.1:8000/ to view the server running in development mode.
8. Make your changes, then commit and push them. Initiate a pull request targeting the `learningequality/ka-lite/develop` branch (by default it may have selected the `master` branch).

### Where does communication happen?

1. Any public, general development questions/announcements can go on the [KA Lite dev Google group](groups.google.com/forum/?fromgroups#!forum/ka-lite-dev). (Join it so you'll receive these messages, too.)
2. Feature requests/bug reports can go on the [GitHub issues page](https://github.com/learningequality/ka-lite/issues).
3. We use a [Trello board for internal dev team feature prioritization and assignment/claiming](https://trello.com/board/ka-lite-programming/507303596f46cc9a38c1c94f) (a communal checklist, essentially). [Join Trello](https://trello.com/signup) and [contact Jamie](http://jamiealexandre.com/contact/) if you'd like to be added to the board.
4. [Like the project on Facebook](https://www.facebook.com/kaliteproject) and [follow it on Twitter](https://twitter.com/ka_lite) to stay in the loop. Also, [subscribe for updates on the main project page](http://kalite.adhocsync.com/).

Guidelines
===

### Priority on efficiency

KA Lite is designed to function reasonably well on low power devices (such as a Raspberry Pi), meaning we want to avoid doing anything computationally intensive. Also, for the cross-device syncing operations, connection bandwidth and speed are often expensive and slow, so we should always try to minimize the amount of data needing to be transferred.

### Python dependencies

Because we want an extremely low friction cross-platform installation process, we only want to depend on Python libraries that are pure Python (no compiled C modules, etc) and cross-platform (i.e., work on both Linux, OSX and Windows). Then, the packages themselves can be fully included in the download codebase without worrying about what platform it was compiled for. Soft dependencies on a package with binaries is fine; e.g., for efficiency reasons, the project takes advantage of `python-m2crypto` if available, but falls back to `python-rsa` (a pure Python implementation) otherwise.

### Python

We roughly try to follow the [PEP8 conventions](http://www.python.org/dev/peps/pep-0008/), with a few exceptions/clarifications:

* Limit line length to 119 characters (PEP8 limits lines to 79 characters, but this can lead to a lot of wrapping)
* We're somewhat flexible in where we put empty lines; the goal is to use empty lines as punctuation to separate semantic units.

### Python 2.6 restrictions

KA Lite lists Python 2.6 or 2.7 as a dependency, and thus any code written needs to be backwards compatible with Python 2.6, meaning:

1. Do not use dictionary comprehensions (e.g. `{num, num**2 for num in range(100)}`).
2. Do not use the `OrderedDict` data structure.
3. Do not use the `argparse` module.
4. Do not use the `viewkeys()`, `viewvalues()`, and `viewitems()` methods of the dict class.
5. Do not define set literals using braces (e.g. `{4,5,6,7}`). Instead, use the set constructor (e.g. `set([4,5,6,7])`).

### CSS

The file `khan-site.css` is from khan-exercises, and we don't want to modify it, in case we want to update it from there in the future. Instead, most CSS styling goes in khan-lite.css, and will override any styles defined in `khan-site.css`. For styles that will only ever be used on a single page, they can be defined in a `<style>` block inside `{% block headcss %}`. Avoid using inline (tag attribute) styles at all costs.