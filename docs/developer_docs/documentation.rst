How to contribute to documentation
==================================

You can propose changes to the docs directly on Github (instructions below) or
email your recommendations to info@learningequality.org.

To propose changes directly, you'll need to create an account on github and open
a pull request. This document assumes you are somewhat familiar with that
process, and will not explain all the steps in detail. For full instructions on
how to make a pull request, see
`Github's help section <https://help.github.com/articles/creating-a-pull-request/>`_.

Documentation development
-------------------------

#. Work from the *develop* branch.
#. From the base directory, the documentation can be found in the ``docs/``
   subdirectory. Specific pages of the docs are each associated with a different
   .rst file, potentially in a subdirectory of ``docs/``.
#. The documentation is written in
   `ReStructured Text <http://sphinx-doc.org/rest.html>`_ format, so please see
   the primer!
#. After making your changes, try to build the docs to review them. This process
   can take some time, as an instance of the server and a browser may need to
   be started. To build the docs::
   
       pip install -r requirements_sphinx.txt  # To install software for building docs
       cd docs
       make html

#. You can view the docs in a browser by opening *docs/_build/html/index.html*.
#. After you are satisfied with your changes push them to your fork of the ka-lite project, and then open a PR.
