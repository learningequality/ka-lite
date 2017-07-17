KA Lite
=======

by `Learning Equality <https://learningequality.org/>`__

|Build Status| |Coverage Status| |Docs|

.. |Build Status| image:: https://circleci.com/gh/learningequality/ka-lite/tree/develop.svg?style=svg
   :target: https://circleci.com/gh/learningequality/ka-lite/tree/develop

.. |Coverage Status| image:: http://codecov.io/github/learningequality/ka-lite/coverage.svg?branch=develop
  :target: http://codecov.io/github/learningequality/kolibri?branch=develop

.. |Docs| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat
   :target: http://ka-lite.readthedocs.org/

`Khan Academy <http://www.khanacademy.org/>`__'s core mission is to
"provide a free world-class education for anyone anywhere", and as over `60%
of the world's population is without access to the
internet <http://en.wikipedia.org/wiki/Global_Internet_usage>`__,
primarily in the developing world, providing an alternative delivery
mechanism for Khan Academy content is key to fulfilling this mission.

`KA Lite <http://kalite.learningequality.org/>`__ is a lightweight
`Django <https://www.djangoproject.com/>`__ web app for serving core
Khan Academy content (videos and exercises) from a local server, with
points and progress-tracking, without needing internet connectivity.

Primary use cases include:
--------------------------

-  For servers/\ **computer labs located in remote schools**, which
   could be slowly syncing with a central server over a cell/satellite
   network or via USB keys.
-  In **correctional facilities** and other environments where providing
   educational materials is of value, but users cannot be given general
   internet access.
-  **Mobile school "vans"**, which transport a server and multiple
   laptops/tablets between a number of schools (or orphanages, community
   centers, etc) in remote communities on a rotating basis, and syncing
   up with a central database (to download new content and upload
   analytics) when in an area with internet connectivity.

Get involved!
-------------

-  Learn how you can contribute code on our `KA Lite GitHub Wiki <https://github.com/learningequality/ka-lite/wiki>`__
-  Report bugs by `creating issues <https://github.com/learningequality/ka-lite/wiki/Report-Bugs-by-Creating-Issues>`__
-  Read more about the project's motivation at `Introducing KA Lite, an offline version of Khan
   Academy <http://jamiealexandre.com/blog/2012/12/12/ka-lite-offline-khan-academy/>`__.

Roadmap
-------

Later in 2017, Learning Equality will be launching the successor of KA Lite. It's
called `Kolibri <http://github.com/learningequality/kolibri>`__ and will have
very similar features to KA Lite, but will also be a platform for many other
educational resources besides Khan Academy's.

Because of the popularity of KA Lite, we are continuing
to support deployments by providing fixes to problems that
directly affect current usage. These include issues related to new
browsers, operating systems etc. We are also still optimizing regarding
performance issues.

If you are creating a new deployment at this very moment, feel assured that
KA Lite is still alive and will be maintained for the rest of 2017, after which
point we will be recommending that you migrate to Kolibri.

In the meantime, if you need new features in KA Lite, we welcome you to join
the community and contribute. In other words, we (Learning Equality) encourages
you (community members), to feel empowered and take responsibility for the
future of KA Lite.

Connect
^^^^^^^

- Community forums: `community.learningequality.org <https://community.learningequality.org/>`__
- IRC: **#kalite** on Freenode
- Twitter: `@ka_lite <http://twitter.com/ka_lite>`__

Contact Us
^^^^^^^^^^

Tell us about your project and experiences!

-  Email: info@learningequality.org
-  Add your project to the map: https://learningequality.org/ka-lite/map/

License information
-------------------

The KA Lite sourcecode itself is open-source `MIT
licensed <http://opensource.org/licenses/MIT>`__, and the other included
software and content is licensed as described in the
`LICENSE <https://raw.github.com/learningequality/ka-lite/master/LICENSE>`__
file. Please note that KA Lite is not officially affiliated with, nor
maintained by, Khan Academy, but rather makes use of Khan Academy's open
API and Creative Commons content, which may only be used for
non-commercial purposes.
