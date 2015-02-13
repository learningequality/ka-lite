Linux Installation Guide
===========================
.. note:: You will need to make sure *sudo* is installed for both Debian and Ubuntu. These commands can then be used for both operating systems. 

.. note:: Type the following commands in a terminal.

#. Check if Python is already installed with *python -V*.
#. If not already installed or outdated, install Python v2.6 (*sudo apt-get install python2.6*) or v2.7 (*sudo apt-get install python2.7*).
	* Or use your Distro's Package Manager by searching for *Python*.
#. If not already installed or outdated, install Git with *apt-get install git-core*.
	* Or use your Distro's Package Manager by searching for *Git*.
#. Switch to the directory in which you wish to install KA-Lite.
#. Enter *git clone https://github.com/learningequality/ka-lite.git* to download KA Lite.
#. Switch into the newly downloaded ka-lite directory
#. Run the install script with *./setup_unix.sh*.
#. **IF** you want the server to start automatically in the background after your server starts then:
	* Setup the server (one time) to automatically run in the background
	* Enter *sudo ./runatboot.sh* in the terminal from inside the ka-lite/kalite directory
	* Use *sudo service kalite stop* to stop the server
	* OR *sudo service kalite start* to start the server.
#. **IF** the automatic background option was not chosen, start the server by running *./start.sh* in the ka-lite directory.
#. KA Lite should be accessible from http://127.0.0.1:8008/ 
	* Replace *127.0.0.1* with the computer's external IP address or domain name to access it from another computer.


