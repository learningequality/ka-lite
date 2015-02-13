## Requirements
You need to install following dependecies in order to build the docs in headless mode:
- xvfb (system package)
- pyvirtualdisplay (python package)

You'll also need to install `sphinx`.

Execute following commands as root user to install the dependencies.
For ubuntu users:
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

## Builiding Documentation
Change your current working directory to `sphinx-docs` directory under `ka-lite` root and execute following command:
```
    make html
```
If the above command executes successfully, docs should be found under `sphinx-docs/_build` directory inside `ka-lite`.
