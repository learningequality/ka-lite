How to contribute to documentation
==================================

You can propose changes to the docs directly on github (instructions below) or email your recommendations to info@learningequality.org.

To propose changes directly, you'll need to create an account on github and open a pull request. This document assumes you are somewhat familiar with that process, and will not explain all the steps in detail. For full instructions on how to make a pull request, see `Github's help section <https://help.github.com/articles/creating-a-pull-request/>`_. Some guidelines:

* Work from the *develop* branch.
* From the base directory, the documentation can be found in the *sphinx-docs* subdirectory. Specific pages of the docs are each associated with a different .rst file, potentially in a subdirectory of *sphinx-docs*.
* The documentation is written in `ReStructured Text <http://sphinx-doc.org/rest.html>`_ format, so please see the primer!
* After making your changes, try to build the docs to review them. This process can take some time, as an instance of the server and a browser may need to be started. To build the docs (see *README.md* in the *sphinx-docs* directory for requirements):

    * In Linux, if you have the *pyvirtualdisplay* package installed you can build in headless mode by running the command *env SPHINX_SS_USE_PVD=true make html* in the *sphinx-docs* directory.
    * In other OSes, or to build in non-headless (headed?) mode, just run the command *make html* in the *sphinx-docs* directory. This may launch a browser. Don't interfere with it!

* You can view the docs in a browser by opening *sphinx-docs/_build/html/index.html*.
* After you are satisfied with your changes push them to your fork of the ka-lite project, and then open a PR.

For this project we have created an rst directive to take screenshots of the site (in case of UI changes or to build internationalized versions of the docs). To read about the use of this directive, see the *SCREENSHOT_USAGE.md* file and check out usage in the docs (a good starting point is the ss_examples.rst file).
