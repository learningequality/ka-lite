## Requirements
You need to install following dependencies in order to build the docs in headless mode:
- xvfb (system package)
- pyvirtualdisplay (python package)

You'll also need to install `sphinx`.

Execute following commands as root user to install the dependencies.
For Debian/Ubuntu users:
```
    apt-get install xvfb
```
For RHEL/CentOS/Fedora users:
```
    yum install xorg-x11-server-Xvfb
```

Then, install following python packages:
```
    pip install pyvirtualdisplay
    pip install sphinx
```
 

## Building Documentation
Change your current working directory to `docs` directory under `ka-lite` root and execute following command:
```
    make html
```
If the above command executes successfully, docs should be found under `docs/_build` directory inside `ka-lite`.

## Building translated docs
1. Make sure you have the sphinx-intl dependency (run the command `pip install -r requirements` in this directory).
2. Extract the translatable messages into pot files using the command `make gettext`. The pot files are then found in `_build/locale directory`.
3. Setup po files for your target language with the command `sphinx-intl update -p _build/locale -l xx`, where xx is the language code of your target language (i.e. "de" or "eo"). (Note: running the `update_pot` command from the central server will generate po files and grab them for uploading.)
4. Translate the po files in `locale/xx/LC_MESSAGES`. TODO: Automate this.
5. Build the mo files with `sphinx-intl build`
6. Make the docs in the target language with the command `make -e SPHINXOPTS="-Dlanguage='xx'" html`
7. Party time!
