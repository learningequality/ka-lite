
Admininistrator User Manual
============================
**Who is an "administrator"?**

A person who :
    * helps to plan and oversee a project using KA Lite
    * installs and updates KA Lite
    * can create coach logins, Learner logins, download videos and language packs

Administrator Glossary
-------------------------------------------
For users that choose to register online, there are some important terms to familiarize yourself with so that you understand how the flow of data works between installations and the online data hub.

**Sharing Network**
	A sharing network is a group of devices that share data between one another. Data can mean video content, access software applications, and certain files.

**Organization**
	An organization is a group of people responsible for administering a set of Sharing Networks. An organization can have multiple administrators and manage multiple sharing networks.

**Facility**
	A facility is the physical space in which a device is located (e.g. a school or a computer lab in a community center). Learner, coach, and admin accounts are associated with a particular facility.

**Device**
	A device should be able to run a KA Lite server (most computers) and other devices to be used as clients. One common configuration is using a Raspberry Pi or other inexpensive computer as a server and relatively cheap tablets as client devices. Tablets can access the servers through an access point, such as a Wi-Fi dongle, or some other networking device such as a router.

**Torrent**
    A file or files sent using the BitTorrent protocol. It can be any type of file, such as a movie, song, game, or application. During the transmission, the file is incomplete and therefore referred to as a torrent. Torrent downloads that are incomplete cannot be opened as regular files, because they do not have all the necessary data.

**Seeder**
    Seeders are users who have a complete version of the file you wish to download. If there are no seeders for a particular file, you will not be able to download the file. Seeders are extremely important, for they help distribute the file.

**Bandwidth**
    The amount of data that an Internet connection can handle in a given time. An Internet connection with larger bandwidth can move a certain amount of data much faster than an Internet connection with a lower bandwidth.

Accessing KA Lite **THIS NEEDS UPDATING, BUT VERY IMPORTANT**
-------------------
In order to access KA Lite after it has been successfully installed, please grab the URL given at the end of the installation process (http://127.0.0.1:8008/) **this will probably have to be changed later!!!! tHERE ARE A LOT OF THINGS THAT NEED TO BE CHANGED**

Setting up KA Lite
-------------------
Once you have successfully installed KA Lite, the installation script should give you a URL (http://127.0.0.1:8008/) to visit so that you can open KA Lite and login for the first time. 

Copy and paste the URL into a web browser. The KA Lite application should show up.  and login to KA Lite using the username and password you created during the installation process. 

* If you have forgotten the username/password combination, simply delete this version of KA Lite (delete the “ka-lite” folder that you downloaded during the installation guide steps for your system and then redo the installation steps in the Install Guide). If it is critical that you are able to login with your credentials, :doc:`../contact` and we can help you manually reset your login information.

Once you’ve logged in, the next step in the setup process is registering your device with the KA Lite Hub.

Registering Your Device with the Hub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By registering your device with FLE, you can sync data back with our central data hub. This is useful for many reasons:

    #. a project administrator can manage user accounts and view usage data from afar, without needing to physically visit the offline device.
    #. usage data syncing back can inform the FLE team of multiple users in a certain geographic region, and we can connect people that might be able to help one another
    #. it helps FLE and our partners understand where and how the software is being used, so we can keep adding features that support you! 

You will have two options: 

    #. **One click registration**. This is the perfect option for individual users who just want to get KA Lite up and running fast, and don't need online access to data. This allows you to get the registration process over in one-click without worrying about creating a login that you're never going to use. **Caution**: if you choose to one-click register, you will unable to register with online access to data later. (If you chose this option by accident and would like to start over, please see **PUT LINK ON HOW TO START OVER**).


    #. **Register with online access to data**. Choose this option if you're an administrator of larger projects. This option allows you to access your uploaded data and connect multiple installations to the same account. 

How to register your device with online access to data
########################################################


**system currently down, this needs updating later**




Post Registration Setup
-------------------------------------------
Now that you have registered successfully, it's time to configure your local KA Lite installation to suit your needs. If any terms like 'facility' or 'device' become confusing, feel free to reference the `Administrator Glossary`_ for a quick reminder.


Create a Facility
-------------------------
KA Lite assumes that you are going to be using the software primarily in one place. This could be a school, a home, a community center, etc. We call this place a “facility”, and use it to help differentiate users who are syncing back data with our central data hub. In order to create a facility, follow the steps below.

#. Log in to KA Lite.
#. Click the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Under the Facilities section, click on "Add a new facility..."
#. Fill in the information for all the fields you find below the map
#. Click the "Save facility" button when you are finished.
#. Once the information has been saved, you will be redirected back to the "Facilities" page, where you will see a message indicating that you have successfully saved your new facility.


Delete a Facility
-------------------------
#. Log in to KA Lite.
#. Click the "Manage" tab at the top of the page. 
#. Make sure that the "Facilities" tab is selected.
#. Find the facility you would like to delete, and click the trash can icon to delete the facility.
#. You will be prompted to type in the name of the facility you wish to delete for confirmation.
#. If your delete is successful, you will be redirected back to the "Facilities" page, where you will see a message indicating that you have successfully deleted the facility.

User Management
-------------------------
Coaches and learners are the other types of users that KA Lite supports. In order for them to be able to login, you need to create accounts for them.

Adding Learners
^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Select the facility that the learner will belong to.
#. Under the "Learners" header, click on "Add a new Learner".
#. You will be redirected to a page that says "Add a new Learner". Select the facility this Learner belongs to, and fill in all the information.
#. Click "Create user". You should be redirected to the "Facilities" page, where you will see a message indicating that you have successfully created a Learner user. 

Permanently Deleting Learners
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Under the "Facilities" header, select the facility the Learner belongs to.
#. Under the "Learners" header, mark the box to the left of the Learner account you would like to delete.
#. Press the "Delete Learners" button.
#. You will be prompted with a confirmation of your deletion. Press "OK" to proceed with the deletion.

Adding Learners
^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Select the facility that the coach will belong to.
#. Under the "Coaches" header, click on "Add a new coach".
#. You will be redirected to a page that says "Add a new coach". Select the facility this coach belongs to, and fill in all the information.
#. Click "Create user". 
#. If the user was successfully created, the page will reload with a message indicating that you have created the user.

Permanently Deleting Coaches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Under the "Facilities" header, select the facility the coach belongs to.
#. Under the "Coaches" header, mark the box to the left of the coach account you would like to delete.
#. Press the "Delete Coaches" button.
#. You will be prompted with a confirmation of your deletion. Press "OK" to proceed with the deletion.

Adding a Group
^^^^^^^^^^^^^^^^^^^^^^^^^^
You can create groups within a facility. Each group can represent a classroom, a study group, or any other way you would like to group Learners. To create a group, follow the instructions below:

#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Select the facility that the group will belong to.
#. Under the "Learner Groups" header, click on "Add a new group".
#. Fill out the name of the group, and provide a description.
#. Click "create group".
#. You should be redirected back to the page for the facility. If the group was successfully created, you will see it listed under the "Learner Groups" section.

Deleting a Group
^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Log in to KA Lite.
#. Click on the "Manage" tab at the top of the page.
#. Make sure that the "Facilities" tab is selected.
#. Mark the box to the left of the group you would like to delete.
#. Press the "Delete Groups" button under the "Learner Groups" header.
#. You will be prompted with a confirmation of your deletion. Press "OK" to proceed with the deletion.


Moving a User to a New Group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Navigate to the page for the facility the user belongs to.
#. Under the "Learners" header, select the Learner you would like to move by clicking in the checkbox to the left of the Learner name.
#. In the dropbox, select the group you would like to move the user to.
#. Click the "Change Learner Groups" button.
#. The page will refresh, with a message at the top indicating a successful move.

Removing Users from a Group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you'd like to remove a user from a group without permanently deleting the user, please follow the instructions below:

#. 




Group Summary Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For each group, you should be able to view some statistics. 

#. Navigate to the Learner Groups section of the facility you wish to look at. 
#. Click on the group that you wish to view.
#. The statistics for the group should be displayed at the top of the page.

Edit User Information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 
#. Navigate to the page for the facility that the user belongs in.
#. Find the user you would like to edit.
#. Click the blue pencil |bluepencil| icon next to the name of the user that you would like to edit.
#. Make all necessary changes on the edit user page, and click "Update user".
#. You will be redirected to the previous page, with a message at the top indicating that your changes have been saved.

.. |bluepencil| image:: bluepencil.png

Downloading Videos
---------------------
Now that you've created a facility and user accounts, it's time to add video content to your local KA Lite installation! Since the videos can take up a large amount of space, you can choose to download only the videos that you need. If your device has enough space and you wish to download all of the videos, we recommend skipping to `Downloading Videos in Bulk`_ . 


Downloading Individual Videos
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Click the "Manage" tab at the top of the page.
#. Click on the "Videos" tab.
#. View subtopics by clicking on the '+' symbol to the left of a subject of your choice. You can cose them by clicking on the '-' symbol.
#. Mark the content you wish to download by clicking the checkbox to the left of the content name. 
#. Click the green "Download" button in the top left box of the page. The button should also show you the total number of videos you have selected to download, as well as the total size of the content.
#. Once the download is completed, video content will be ready for Learners to watch!

Downloading Videos in Bulk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you want to download videos in bulk, your best option is to download the KA Lite videos through the `BitTorrent Sync`_ client. This will be a much faster process than using the KA Lite app to download all of the videos.

We have made the full set of KA videos (in the format needed by KA Lite) available via `BitTorrent Sync`_ (btsync). Note that this is different from BitTorrent; btsync allows us to add new videos or fix problems without issuing a whole new torrent file, and then having seeders split between the old and new torrent files. Here are the steps to set this up:

#. Download and install `BitTorrent Sync`_.
#. Run btsync. On some platforms, this will bring up a graphical interface. On Linux, you will need to load http://127.0.0.1:8888/ to get the interface
#. Click the "Enter a key or link" button, and put in **https://link.getsync.com/#f=ka­lite­compressed&sz=25E9&q=­&s=TOQVB3LLGWCKEQ6NOCFBSEVWA74PRA6I&q=­&i=C4M3QMAVXE7RVXR7B3526TBD5V3KYV 5V6&q=­&p=CCGAGLIJGFQFP2X2Z4QWQ3MLPJHTVV3A** 
#. Select the "content" folder inside your KA Lite installation as the "location" (unless you want the videos to be located elsewhere).
#. Allow the videos to sync in there from your peers! It may take a while for now, as we don't yet have many seeders on it. On that note -- please help seed by keeping it running even after you've got all the videos, if you have bandwidth to spare! This will make it easier for others to download the content as well.

These are resized videos. All in all, this will take around 23 GB of space. 

If you chose to download them to somewhere other than the content folder inside the ka-lite folder as recommended above, you need to tell KA Lite where to find them. If this is the case, follow the steps below:

#. Make sure all video files are located in a single directory, with .mp4 extensions (KA Lite expects this!)
#. If it doesn't already exist, create a file named local_settings.py in the ka-lite/kalite folder (the one containing settings.py)
#. Add the line CONTENT_ROOT="[full path to your videos directory]", making SURE to include an OS-specific slash at the end (See examples) and encapsulate it in quotes. 

        For example, on Windows:
        CONTENT_ROOT="C:\\torrented_videos_location\\"

        For example, on Linux:
        CONTENT_ROOT="/home/me/torrented_videos_location/"

#. Restart your server. If you are unsure on how to do this, please see `Restarting Your Server`_ . 

.. _BitTorrent Sync: http://www.getsync.com/


Language Packs
---------------------------
KA Lite supports internationalization. You can download language packs for your language if it is available. A language pack comes with all the available subtitles and user interface translations for that language. When it is installed, KA Lite will give you the option to download individual dubbed videos from the language's Khan Academy YouTube channel.

Download Language Packs
^^^^^^^^^^^^^^^^^^^^^^^^^
To download language packs: 

#. From the "Manage" page, click on the "Language" tab. 
#. Select the language pack you wish to download by selecting from the drop-down menu.
#. Click the "Get Language Pack" button. 
#. Once the download finishes, you can see your language pack in the list of installed packs. Learners and coaches will now be able to switch their language to any of the installed language packs. Their default will be the default that you set by clicking on "Set as default". 

Delete Language Packs
^^^^^^^^^^^^^^^^^^^^^^^^^
To delete language packs:

#. Log in as the administrator.
#. Click the "Languages" link in the navigation bar
#. In the Installed Languages section, there is a button for deletion of each language.


Restarting Your Server
-----------------------
If you have made some configuration changes (such as changing the filepath to your video content to your liking), or if you feel the need to reboot your KA Lite system, you may want to restart your server. Please note that this will cause KA Lite to become inaccessible to any users. However, this will not delete any user accounts or information that you have configured during set up. 

This process varies, depending on which OS you are running the KA Lite Server on. 

Restarting Your Server: Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Restarting Your Server: Linux
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Restarting Your Server: Mac 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Open up your terminal. You may do this by navigating to the magnifying glass |magglass| at the top right corner of your screen, and typing in "Terminal", then hitting "Enter" on your keyboard.

    .. image:: search.png
        :align: center
        :width: 700
        
#. Your terminal should be opened up. It should look a little something like the following: 

    .. image:: terminal.png 
        :align: center

    Type in "sudo lsof -i :8008" into the prompt, without the quotes. Running this command will prompt you for the machine password. Please enter your machine password, then hit "ENTER" on your keyboard.

#. After entering your password, some information should appear on your screen. Copy the number that appears under "PID". Please note that the number shown will vary, and may not be exactly the same as the one shown in the picture. Loosely speaking, this is the process ID that is currently running your server. We will need its ID in order to stop the process -- in turn, stopping the KA Lite server. 

    .. image:: process.png 
        :align: center

#. Type in "sudo kill -9 <enter PID here>", without quotes into the terminal. Type in the PID that you just copied from the previous step. Be sure to do this without the "< >" symbols. For example, if the PID was the same as the one in the above photo example, you would type in "sudo kill -9 9585". 

#. You may be prompted for your machine password again. If so, please enter in your machine password and hit "Enter" on your keyboard. 

#. Your KA Lite server is now stopped. Now, simply start the KA Lite server as normal. If you are unsure on how to do this, please re-visit `Accessing KA Lite`_ .

.. |magglass| image:: magglass.png


