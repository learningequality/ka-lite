## Requirements
You need to install following dependencies in order to build the docs in headless mode:
- xvfb (system package)
- pyvirtualdisplay (python package)

Execute following commands as root user to install the dependencies.
For Debian/Ubuntu users:
```
    apt-get install xvfb
```
For RHEL/CentOS/Fedora users:
```
    yum install xorg-x11-server-Xvfb
```

Then, in the base directory, run `pip install -r requirements_sphinx.txt`.
 

## Building Documentation
Change your current working directory to `docs` directory under `ka-lite` root and execute following command:
```
    make html
```
If the above command executes successfully, docs should be found under `docs/_build` directory inside `ka-lite`.


## Building Documentation with automatic screenshots
We use Selenium web driver and a custom sphinx directive to take screenshots of the KA Lite application. It takes a 
long time -- an instance of the server is spun up with an in-memory database and user data is generated.

Custom directives in the rst files indicate on which page a screenshot should be taken, and what actions the web driver
instance should do to prepare the screenshot. This is failure-prone if the instructions are based on *timing* (which
could change from machine to machine or even on subsequent runs) much like flaky tests. It's also failure prone if
the UI is changed "from underneath" the directive, for instance by referencing an element id that no longer exists on
that page. Because this command is run infrequently, it's generally not noticed when this happens.

Before building the docs with screenshots, you'll need to create js assets. Run `node build.js` followed by
`kalite manage collectstatic`.

To build the docs with screenshots, add the line `screenshots_create = True` to `conf.py`, then run `make html`.
If the environment variable `SPHINX_SS_USE_PVD` has the value `true`, then screenshots will be made headlessly using
xvfb.

## Building translated docs
1. Make sure you have the sphinx-intl dependency (run the command `pip install -r requirements` in this directory).
2. Extract the translatable messages into pot files using the command `make gettext`. The pot files are then found in `_build/locale directory`.
3. Setup po files for your target language with the command `sphinx-intl update -p _build/locale -l xx`, where xx is the language code of your target language (i.e. "de" or "eo"). (Note: running the `update_pot` command from the central server will generate po files and grab them for uploading.)
4. Translate the po files in `locale/xx/LC_MESSAGES`. TODO: Automate this.
5. Build the mo files with `sphinx-intl build`
6. Make the docs in the target language with the command `make -e SPHINXOPTS="-Dlanguage='xx'" html`
7. Party time!
