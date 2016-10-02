Inline help
===========

In order to write inline help, refer to the file ``kalite/inline/narratives.py``.

You don't have to understand Python to write it really, just reuse the structure
that's already there.

Simple workflow
_______________

You should be able to write inline help for a page following these simple steps:
  
  #. Clone the repository and setup a development environment following the
     steps in :ref:`development-environment`.
  #. Open up the file ``kalite/inline/narratives.py``
  #. Add a new entry of a page you wish to write inline help for, for instance if
     the URL of the page is ``/learn``, then you can add this entry::
          u'learn/?$': [
              {u'#css-id': [
                  {u'step': 1},
                  {u'text':
                      _(u'This is the explanation for the user')}
              ]},
          ],

     .. note:: The URL entry is a regular expression. You might want to implement
              variations of the URL in case it can be parameterized. Do not include
  #. After changing the documentation, you can view the results by running the
     development server from command line::
        bin/kalite manage runserver --settings=kalite.project.settings.dev

Once you written inline help, go and open up a Pull Requestion for the
``develop`` branch on our Github page.

