Frequently Asked Questions
==========================

How do I install KA Lite?
-------------------------

Information on how to install KA Lite is available via our :doc:`user guides </installguide/install_main>`.

How much does KA Lite cost to install?
--------------------------------------

It is **FREE** -- both free as in "free speech" and free as in "free beer"! To learn more about free software, see this `Free Software Foundation article <http://www.fsf.org/about/what-is-free-software>`_.

How do I report a problem?
--------------------------

Please follow the instructions on our `Github Wiki`_ for reporting bugs.

.. _Github Wiki: https://github.com/learningequality/ka-lite/wiki/Report%20Bugs%20by%20Creating%20Issues

Why are my downloaded videos not displaying?
--------------------------------------------

Please refer to :ref:`video-playback`.

How do I change KA Lite's content folder?
-----------------------------------------

If you want to change your installation's content folder from the default (say, to point to a shared folder across installations), see how to configure ``CONTENT_ROOT`` in the ":ref:`configuration-settings`" section.

How do I change the directory where *all* of KA Lite's runtime files go, including content?
-------------------------------------------------------------------------------------------

You can change this directory by setting the ``KALITE_HOME`` environment variable to the path of your choice.

If the variable is left unset (default), KA Lite's runtime files will be placed in your user's home directory under the ``.kalite`` subdirectory. Typically, it is ``/home/user/.kalite/`` (on Windows, locate something like
``C:\Documents and Settings\<username>\.kalite``).

There are many ways to set an environment variable either temporarily or permanently. To start ``kalite`` on OSX or Linux with a different home, run::

    KALITE_HOME=/path/to/home kalite start

The change requires that you first stop the server, change the ``KALITE_HOME`` environment variable, and then copy the contents from the default ``.kalite`` directory to the new directory you just specified. When you start the server again, all your files should be seamlessly detected at that location.

Is there somewhere I can find Spanish language content organized by topic?
--------------------------------------------------------------------------

Yes! Thanks to the efforts of an awesome volunteer deploying KA Lite and other OER in the Sacred Valley in Peru, you can download blocks of Spanish Lanugage content from his public `Google Drive folder`_. You can also follow his deployment at http://www.huacamayu.org/.

.. _Google Drive folder: https://drive.google.com/#folders/0B5qtw8M1ijVVMTF5NU40VVZMbk0

I would like to download the videos for KA Lite via BitTorrent, is this possible?
---------------------------------------------------------------------------------

Yes! Please see the instructions for ":ref:`bulk-video-downloads`".


.. _content_pack_retrieve_offline:

How can I install a language pack without a reliable internet connection?
-------------------------------------------------------------------------

In version 0.16 we changed the proces for making KA Lite available in other languages. For more technical background about the new **contentpacks**, please refer to our `Wiki page <https://github.com/learningequality/ka-lite/wiki/Content-packs>`_.

You can download from our server the new :url-pantry:`contentpacks for all the languages <content/contentpacks/>`, and carry around the zip file to computers you want to install the contentpack to.

Once you have downloaded the contentpack for install on a computer without a reliable internet access, use the following command::

    kalite manage retrievecontentpack local <language code> <path to zip file>

Use the language code indicated below:

    ================ ======
     Language name    Code
    ================ ======
     Arabic           ar
     Bulgarian        bg
     Burmese          my
     Danish           da
     English          en
     French           fr
     German           de
     Hindi            hi
     Kannada          kn
     Lao              lo
     Polish           pl
     Portuguese, BR   pt-BR
     Spanish          es
     Swahili          sw
     Tamil            ta
     Xhosa            xh
     Zulu             zul
    ================ ======

An example invocation for installing the French `contentpack` on Windows would be::

    C:\Python27\Scripts\kalite manage retrievecontentpack local fr fr.zip


After starting up your server, you should now see your new language in the Manage > Language page.

Do I need the internet to run KA Lite?
--------------------------------------

No. The only time you need an internet connection is for the initial download of the content (either to the target device, or to a USB stick that can then be carried or mailed). After installation, you can serve the content from a local server or use it directly on the server device without an internet connection.

How do you operate in the field?
--------------------------------

The Learning Equality team primarily works in our San Diego offices, building software and shaping our roadmap based on our interactions with our partners around the world. We work with individual humanitarians and NGOs of all sizes to help them distribute KA Lite to offline communities around the world.

What are the typical deployment scenarios?
------------------------------------------

A typical school deployment varies depending on whether or not a school already has a computer lab.

School with an existing computer lab: In this case, KA Lite would be deployed as a server on one of the existing computers. Students would connect using client devices over the local intranet.

School with no existing computer lab: For schools that do not have an existing computer lab, a KA Lite deployment would involve obtaining a device that can run as a KA Lite server (most computers) and other devices to be used as clients. One common configuration is using a Raspberry Pi or other inexpensive computer as a server and relatively cheap tablets as client devices.

What are some possible hardware configurations for deploying KA Lite?
---------------------------------------------------------------------

You will need:

1. A computer that is running the KA Lite software (e.g. a desktop computer, laptop, or Raspberry Pi).
2. One or more client devices that have web browsers (laptops, tablets, desktop computers, etc)

Note that for a single-user deployment (1) and (2) can be the same computer, with the browser connecting to the locally running KA Lite server software. To make the software accessible to multiple client devices, you will need to put them on the same local network as the KA Lite device (1), e.g. through a WIFI access point.

To read more details, see :ref:`system-requirements`.

What sort of processing power is required for KA Lite?
------------------------------------------------------

See :ref:`system-requirements`.


What are the operating system (OS) and software requirements for running KA Lite?
---------------------------------------------------------------------------------

KA Lite can run on almost any major operating system: Windows, Linux, and Mac/OSX. The only software dependency is the `Python 2.7 runtime`_.

.. _Python 2.7 runtime: https://www.python.org/downloads/

See :ref:`system-requirements`.

What is data syncing?
---------------------

KA Lite is capable to share your student progress data with a `central data repository <https://hub.learningequality.org/>`_ when you are online. This enables the system to have an online backup of your data, allows you to view your student progress online, and to share your data across multiple KA Lite installations.

Who maintains the KA Lite project?
----------------------------------

KA Lite is created, maintained, and operated by the `Foundation for Learning Equality, Inc`_, a California-based nonprofit organization.

.. _Foundation for Learning Equality, Inc: https://learningequality.org

What is KA Lite's affiliation with Khan Academy?
------------------------------------------------

KA Lite is an independent, open-source project maintained by `Learning Equality`_, and is not officially affiliated with Khan Academy, although they are very supportive of the KA Lite project, and are one of our key partners.

.. _Learning Equality: https://learningequality.org

How can local curriculum be generated?
--------------------------------------

Local content creation is something that Learning Equality intends to build into future `platforms <https://learningequality.org/kolibri/>`_. If you would like to be notified when it is available, subscribe for `updates <https://github.com/learningequality/ka-lite/wiki/Communication%20and%20Coordination>`_, or if you would like to help fund this project, please `click here <https://learningequality.org/give/>`_.

.. _home page: http://kalite.learningequality.org/

How is it possible to compress the content into KA Lite?
--------------------------------------------------------

Users are able to select which videos they wish to download through the user-interface, allowing to customize the amount of space used.

What languages is KA Lite available in?
---------------------------------------

KA Lite was `released with internationalization support`_ on 2014/03/07, including support for a translated interface, dubbed videos, subtitles, and translated exercises. Currently we have varying levels of support Portuguese, Danish, French, Polish, Spanish, and many others. Please `visit our blog`_ for the latest information about language support.

.. _released with internationalization support: https://learningequality.org/blog/2014/i18n-released/

.. _visit our blog: https://learningequality.org/blog/

Can I contribute to KA Lite as a developer?
-------------------------------------------

Yes! KA Lite is an `open source project`_, and developers are encouraged to contribute! If you are interested in developing for KA Lite, check out the `instructions for getting started`_.

.. _open source project: https://github.com/learningequality/ka-lite/

.. _instructions for getting started: https://github.com/learningequality/ka-lite/wiki/Getting%20started

Can I contribute to KA Lite as a translator?
--------------------------------------------

Yes, absolutely! If you would like to contribute to KA Lite as a translator, you can get started over on our `translations and internationalization`_ page on our GitHub Wiki!

.. _translations and internationalization: https://github.com/learningequality/ka-lite/wiki/Internationalization:-Contributing-Translations

Can I contribute even if I don't know how to code?
--------------------------------------------------

Yes! `There are many ways! <https://learningequality.org/ka-lite/#community>`_

How do I find out more?
-----------------------

To stay up-to-date on all our activities, follow our `blog <https://learningequality.org/blog>`_, `Twitter <https://twitter.com/LearnEQ>`_, and `Facebook <https://www.facebook.com/learningequality>`_!

How does Learning Equality measure the impact of KA Lite?
---------------------------------------------------------

Because KA Lite is freely available and designed to run offline, collecting impact data can be challenging.

KA Lite is capable of synchronizing data with our central data repository when an online connection exists.

For the deployments in which we do have direct involvement, we receive updates from our partners with quantitative data from the built-in coach reports and attain qualitative data from our on-site visits. For example, we know that 20 out of 20 students in the Idaho Department of Corrections deployment have passed their GED using KA Lite.

.. _backup:

Backing up data: is there any easy way to do it locally?
--------------------------------------------------------

Yes! Just copy the ``.kalite`` folder, typically located in ``/home/user/.kalite``.
To restore, simply copy the backup data file to the same location. If you have
changed versions, please run::

    kalite manage setup

to guarantee your database is compatible with the current version of KA Lite you have installed!
Note that online data back-ups occur if you "register" your KA Lite installation with an online account on our website.

If you only want to backup the database, locate the ``.kalite/database/`` folder
and copy and restore that one.

I can't get KA Lite to work on Windows! The installation succeeded, but nothing happens!
----------------------------------------------------------------------------------------

KA Lite on Windows is controlled through a task-tray program.
See the :doc:`installation guide <installguide/install_all>` for some more info.


I can't see videos in Firefox on Ubuntu/Debian!
-----------------------------------------------

Install `Ubuntu restricted extras package <https://apps.ubuntu.com/cat/applications/ubuntu-restricted-extras/>`_ in the Ubuntu Software Center.
