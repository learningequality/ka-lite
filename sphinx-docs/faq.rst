Frequently Asked Questions
==========================

How do I install KA Lite?
-------------------------

Information on how to install KA Lite is available via our :doc:`user guides </usermanual/userman_main>`.

How much does KA Lite cost to install?
--------------------------------------

It is **FREE** -- both free as in "free speech" and free as in "free beer"! To learn more about free software, see this `Free Software Foundation article <http://www.fsf.org/about/what-is-free-software>`_

How do I report a problem?
--------------------------

Please follow the instructions on our `Github Wiki`_ for reporting bugs.

.. _Github Wiki: https://github.com/learningequality/ka-lite/wiki/Report%20Bugs%20by%20Creating%20Issues

How do I change KA Lite's content folder?
-----------------------------------------

If you want to change your installation's content folder from the default (say, to point to a shared folder across installations), here are the steps you need to do:

#. If it doesn't already exist, create a file named local_settings.py in the ka-lite/kalite folder (the one containing settings.py)
#. Add the line ``CONTENT_ROOT="[full path to your videos directory]"``, making SURE to include an OS-specific slash at the end (see examples) and encapsulate it in quotes.
    **For example, on Windows:** ``CONTENT_ROOT="C:\\videos_location\\"``

    **For example, on Linux:** ``CONTENT_ROOT="/home/me/videos_location/"``
#. Restart your server. If you are unsure on how to do this, please see :ref:`restarting-your-server`.


Is there somewhere I can find Spanish language content organized by topic?
--------------------------------------------------------------------------

Yes! Thanks to the efforts of an awesome volunteer deploying KA Lite and other OER in the Sacred Valley in Peru, you can download blocks of Spanish Lanugage content from his public `Google Drive folder`_. You can also follow his deployment at http://www.huacamayu.org/.

.. _Google Drive folder: https://drive.google.com/#folders/0B5qtw8M1ijVVMTF5NU40VVZMbk0

I would like to download the videos for KA Lite via BitTorrent, is this possible?
---------------------------------------------------------------------------------

We have made the full set of KA videos (in the format needed by KA Lite) available via `BitTorrent Sync (btsync)`_ (note that this is different from BitTorrent; btsync allows us to add new videos or fix problems without issuing a whole new torrent file and then having seeders split between the old and new torrent files) Here are the steps to set this up:

* Download and install BitTorrent Sync
* Run btsync. On some platforms, this will bring up a graphical interface. On Linux, you will need to load http://127.0.0.1:8888/ to get the interface.
* Click the "Enter a key or link" button, and enter  ::

    BT7AOITNAIP3X3CSLE2EPQJFXJXMXVGQI

* Then select the "content" folder inside your KA Lite installation as the "location" (unless you want the videos going somewhere else).
* Allow the videos to sync in there from your peers! It may take a while for now, as we don't yet have many seeders on it. On that note -- please help seed by keeping it running even after you've got all the videos , if you have the bandwidth to spare! This to will make it easier for others to download the content as well.
* Please note that these are resized videos. All in all, this will take around 23GB of space.



Once you have the videos, you need to tell KA Lite where to find them by following the instructions in the :doc:`user guide </usermanual/userman_main>` for your version.

.. _BitTorrent Sync (btsync): http://www.bittorrent.com/sync

Do I need the internet to run KA Lite?
--------------------------------------

No. The only time you need an internet connection is for the initial download of the content (either to the target device, or to a USB stick that can then be carried or mailed). After installation, you can serve the content from a local server or use it directly on the server device without an internet connection.

Is KA Lite involved in getting devices into the hands of students, families, and communities?
---------------------------------------------------------------------------------------------

Currently, KA Lite does not distribute any devices. We are working with partner organizations who do directly distribute devices to local students and communities, and KA Lite is open to any organization who would like to help in this regard. If your organization wants to help KA Lite distribute devices, you can contact us at info@learningequality.org.

How do you operate in the field?
--------------------------------

The FLE team primarily works in our San Diego offices, building software and shaping our roadmap based on our interactions with our partners around the world. We work with individual humanitarians and NGOs of all sizes to help them distribute KA Lite to offline communities around the world.

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

Note that for a single-user deployment (1) and (2) can be the same computer, with the browser connecting to the locally running KA Lite server software. To make the software accessible to multiple client devices, you will need to put them on the same local network as the KA Lite device (1), e.g. through a router.

What sort of processing power is required for KA Lite?
------------------------------------------------------

KA Lite has very low processing requirements, and can be run as a server on devices with processors as low-powered as the $35 Raspberry Pi, using about 100MB of RAM. There is also low processing power required for client devices as well, and any browser that supports HTML5 video with h264 encoding or Flash Player should be able to function as a client device.

What are the operating system (OS) and software requirements for running KA Lite?
---------------------------------------------------------------------------------

KA Lite can run on almost any major operating system: Windows, Linux, and Mac/OSX. The only software dependency is the `Python 2.7 runtime`_.

.. _Python 2.7 runtime: https://www.python.org/downloads/

What is data syncing?
---------------------

KA Lite is capable to share your student progress data with a central data repository when you are online. This enables the system to have an online backup of your data, allows you to view your student progress online, and to share your data across multiple KA Lite installations.

Does KA Lite support peer to peer synchronization?
--------------------------------------------------

Not yet. Peer to peer sync is a priority for KA Lite in the near future, but is not available yet.

Who maintains the KA Lite project?
----------------------------------

KA Lite is created, maintained, and operated by the `Foundation for Learning Equality, Inc`_, a California-based nonprofit organization.

.. _Foundation for Learning Equality, Inc: http://learningequality.org

What is KA Lite's affiliation with Khan Academy?
------------------------------------------------

KA Lite is an independent, open-source project maintained by a distributed team of volunteers, and is not officially affiliated with Khan Academy, although they are (unofficially) very supportive of the KA Lite project.

How can local curriculum be generated?
--------------------------------------

Local content creation is something that KA Lite intends to pursue in the future. This feature is not available at this time, but steps are being taken, as you can read about `here <https://learningequality.org/blog/2013/bringing-ka-lite-gitwe/>`_. If you would like to be notified when it is available, subscribe for updates on our `home page`_, or if you would like to fund this project, please click `here <https://learningequality.org/give/>`_.

.. _home page: http://kalite.learningequality.org/

How is it possible to compress the content into KA Lite?
--------------------------------------------------------

First, users are able to select the amount of videos and exercises they wish to download on the user-interface, allowing the users to customize the size of the files. Also, we have resized much of the content, and approximately 4,000 videos are around 25 GB if downloaded via BitTorrent and around 70 GB via the user-interface.

What languages is KA Lite available in?
---------------------------------------

KA Lite was `released with internationalization support`_ on 2014/03/07, including support for a translated interface, dubbed videos, subtitles, and translated exercises. Currently we have varying levels of support Portuguese, Danish, French, Polish, Spanish. Please `visit our blog`_ for the latest information about language support.

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

Can I contribute even if I don’t know how to code?
--------------------------------------------------

Yes! `There are many ways! <https://learningequality.org/ka-lite/#community>`_

How do I find out more?
-----------------------

To stay up-to-date on all our activities, follow our `blog <https://learningequality.org/blog>`_, `Twitter <https://twitter.com/LearnEQ>`_, and `Facebook <https://www.facebook.com/learningequality>`_!

What can be done with progress tracking during offline usage?
-------------------------------------------------------------

KA Lite's built-in coach reports are meant to provide teachers and administrators access to progress tracking offline. When a student connects back up to the server that they sync with, all of their progress data will be uploaded for teachers and administrators to evaluate.

How does FLE measure the impact of KA Lite?
-------------------------------------------

Because KA Lite is freely available and designed to run offline, we are not in contact with many of our deployments, and collecting impact data can be challenging.

KA Lite is capable to synchronize data with our central data repository when an online connection exists.

For the deployments in which we do have direct involvement, we receive updates from the administrator’s with quantitative data from the built-in coach reports and attain qualitative data from our on-site visits. For example, we know that 20 out of 20 students in the Idaho Department of Corrections deployment have passed their GED using KA Lite.

We are also developing RCTs to start in June for a deployment in India.

Backing up data: is there any easy way to do it locally?
--------------------------------------------------------
Yes! Just copy the file::

    ka-lite/kalite/database/data.sqlite

to a secure location. To restore, simply copy the backup data file to the same location. If you have changed versions, please run::

    python kalite/manage.py migrate --merge

to guarantee your database is compatible with the current version of KA Lite you have installed!
Note that online data back-ups occur if you "register" your KA Lite installation with an online account on our website.
