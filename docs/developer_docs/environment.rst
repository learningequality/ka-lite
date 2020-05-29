.. _development-environment:

Getting started
===============

.. tip:: Find additional knowledge in `Getting Started on our Github Wiki <https://github.com/learningequality/ka-lite/wiki/Getting-started>`_.

KA Lite is discontinued and thus contains several legacy and end-of-life. It is recommended that you set up your development environment in a virtual machine, for instance using `Virtualbox <https://www.virtualbox.org/>`__.

Ubuntu 18.04 LTS
________________

To avoid walking down an uncertain path when you set up this project, consider using Ubuntu 18.04 LTS in a virtual machine.

These steps are largely based on the ``Dockerfile`` from the repository's root.

#. Install prerequisits. The development environment needs Python 2.7, pip and curl.

   .. code-block:: bash
   
      sudo apt install python2.7 curl python3-pip git make

#. Add the nodejs 6.x repo and install it.

   .. code-block:: bash

      # Get the key and add the repo
      wget -qO- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
      echo 'deb https://deb.nodesource.com/node_6.x bionic main' | sudo tee /etc/apt/sources.list.d/nodesource.list

      # Overrule the newer version shipped by Ubuntu
      printf "Package: *\nPin: origin deb.nodesource.com\nPin-Priority: 600" | sudo tee /etc/apt/preferences.d/nodejs

      # Update and install
      sudo apt update
      sudo apt install nodejs

#. Fork the project on `github`_, clone the git repository

      git clone git@github.com:USERNAME/ka-lite.git
      cd ka-lite

#. Create a virtual environment and activate it:

   .. code-block:: bash

      pip3 install virtualenv
      virtualenv -p python2.7 venv
      
      # Activate the virtualenv - you need to do that everytime you open a new command line
      source venv/bin/activate

#. Install a development version of KA Lite inside the virtual environment:

   .. code-block:: bash

      pip install -e .

#. Install development requirements:

   .. code-block:: bash

      # Development
      pip install -r requirements_dev.txt
      # Building docs
      pip install -r requirements_sphinx.txt
      # Test requirements
      pip install -r requirements_test.txt

#. Install JavaScript (nodejs) libraries and build them:

   .. code-block:: bash

      make assets

#. You are now ready to run KA Lite. You can run a foreground version of the HTTP server like this:

   .. code-block:: bash

      kalite start --foreground

#. Run the setup, which will bootstrap the database::
     
   .. code-block:: bash

     kalite manage setup

#. Run a development server and use development settings like this::
     
   .. code-block:: bash

     kalite manage runserver --settings=kalite.project.settings.dev

.. tip:: You can also change your ``~/.kalite/settings.py`` to point to ``kalite.project.settings.dev`` by default, then you do not have to specify `--settings=...` every time you run kalite.

Every time you work on your development environment, remember to switch on your virtual environment with ``source venv/bin/activate``. You can use `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`__ for more convenient ways of managing virtual envs.

.. _github: https://github.com/learningequality/ka-lite


Static vs. Dynamic version
__________________________

Apart from Python itself, KA Lite depends on a couple of Python applications,
mainly from the Django ecosystem. These dependencies can be installed in two ways:

* **Dynamic**: Means dependencies are automatically installed through
  *PIP* as a separate software package accessible to your whole system. This
  is recommended if you run KA Lite and have internet access while installing
  and updating.
* **Static**: Static means that KA Lite is installed with all the external
  dependencies bundled in. Use this method if you need to have KA Lite
  installed from offline media or if KA Lite's dependencies are in conflict
  with the system that you install upon.


Virtualenv
__________

You can install KA Lite in its very own separate environment that does not
interfere with other Python software on your machine like this::

    pip install virtualenv virtualenvwrapper
    mkvirtualenv my-kalite-env
    workon my-kalite-env
    pip install ka-lite


Running tests
_____________


Ensure that you install the test requirements::

    pip install -r requirements_test.txt

To run all of the tests (this is slow)::

    kalite manage test

To skip BDD tests (because they are slow)::

    kalite manage test --no-bdd

To run a specific test (not a BDD test), add an argument ``<app>.<TestClass>``::

    kalite manage test updates.TestDownload --no-bdd

To run a specific item from :ref:`bdd`, use ``<app>.<feature_module_name>``::

    kalite manage test distributed.content_rating --bdd-only

