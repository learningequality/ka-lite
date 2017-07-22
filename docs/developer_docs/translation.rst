Translating KA Lite
===================

We release a "content pack" for a language once a sufficient portion of the
content (videos and user interface) have been translated.

There are two aspects to translation of KA Lite:

* Translating the KA content itself (dubbing videos, subtitling, and translating
  titles/descriptions). This is done
  `through Khan Academy <https://www.khanacademy.org/contribute>`__. Only videos
  that are included on official Khan Academy YouTube language channels, and
  mapped to their English counterparts in Khan Academy's API, will be included
  in KA Lite. 

* Translating the KA Lite interface text. For user interface translations, we
  use a website called CrowdIn. In order to contribute translations, follow the
  steps below: 

    1. Sign up for the
       `KA Lite Volunteer Translation Group <https://groups.google.com/a/learningequality.org/forum/#!forum/i18n>`__.
    2. Create an account on
       `CrowdIn <https://crowdin.net/project/ka-lite>`__, our online
       translations portal.
    3. Start contributing translations on CrowdIn! You will want to focus on the
       files for the version you're targeting -- for instance, to translate the
       strings for KA Lite 0.14, you should focus on translating strings in
       ``0.14-django.po`` and ``0.14-djangojs.po``.


Creating new source translations
--------------------------------

Facilitators of CrowdIn should do the following each time that a new major
release approaches:
  
  1. Navigate to the root of your ka-lite git checkout. Make sure your
     environment is activated.
  2. Run::

         make msgids

  3. After this, you should have updated files in ``locale/``.
  4. Commit the files to Github in a PR and have them merged. We track these
     changes in Git to ensure a transparent mechanism for changes.
  5. Upload the files with their versioned file names to CrowdIn.

Legacy
------

Our translations have worked slightly differently since they were introduced in
0.11. On CrowdIn, we have older versions avaiable, for which 0.14 through to
0.16 all contain translation strings from the central server (the one running
on hub.learningequality.org).

As of 0.17, we have started to maintain the English source messages in Git and
will sync them to CrowdIn after each string freeze.

