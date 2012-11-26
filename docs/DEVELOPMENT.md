How to contribute
===

Firstly, thank you for being willing to offer your time to contribute to the KA Lite efforts! The project is run by volunteers dedicated to helping make educational materials more accessible to those in need, and every contribution makes a difference.

### Getting started

1. Fork the main KA Lite repository (signing up for a GitHub account first, if needed).
2. Follow the [installation instructions](../INSTALL.md), except clone your own repo instead of the main repo:
(e.g. `git clone --recursive git@github.com:YOURACCOUNTNAME/ka-lite.git`)
3. Switch to the `develop` branch, which is where any commits you make should go: `git checkout develop` (we are roughly following the [successful git branching model](http://nvie.com/posts/a-successful-git-branching-model/) conventions)
4. In the `ka-lite/kalite` directory, add a file called `local_settings.py`, and put `DEBUG = True` in it.
5. Open two terminal/shell windows, in the `ka-lite/kalite` directory. In one, run `python manage.py runserver` (to start the Django development server), and in the other, run `python manage.py cronserver 5` (to run the background processing script, which does things like download requested videos).

Guidelines
===

### Priority on efficiency

KA Lite is designed to function reasonably well on low power devices (such as a Raspberry Pi), meaning we want to avoid doing anything computationally intensive. Also, for the cross-device syncing operations, connection bandwidth and speed are often expensive and slow, so we should always try to minimize the amount of data needing to be transferred.

### CSS

The file `khan-site.css` is from khan-exercises, and we don't want to modify it, in case we want to update it from there in the future. Instead, most CSS styling goes in khan-lite.css, and will override any styles defined in `khan-site.css`. For styles that will only ever be used on a single page, they can be defined in a `<style>` block inside `{% block headcss %}`. Avoid using inline (tag attribute) styles at all costs.

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

### Python package dependencies

We want to be able to include all required Python packages as part of the main repository, which means they must be pure Python (no compiled C modules, etc) and cross-platform (i.e., work on both Linux and Windows).

