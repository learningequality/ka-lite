Raspberry Pi Installation Guide
================================
Please follow *steps 1-8* for normal Linux Installation Guide.

During installation you will be asked to optimize your installation for performance on the Raspberry Pi.

Say **YES!** Make sure you have a stable Internet connection during the process, as you will be downloading a number of 3rd party open source libraries.

Raspberry Pi Wi-Fi
------------------------------
.. note:: Two Wi-Fi USB modules have been tested with KA Lite on the Raspberry Pi
	
	* Raspberry Pi WiPi adaptor
	* Edimax EW-7811Un
In our tests, we found that the WiPi adaptor supported a higher number tablet connections.
	
Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. note:: The Raspberry Pi may crash if the USB adaptor is inserted or removed while the computer is switched on.
	
	* Make sure to shutdown and remove the power from the Raspberry Pi.
	* Afterwards, insert the wireless USB adaptor.
	* Lastly, switch the Raspberry Pi on.

#. Make sure the Raspberry Pi operating system is up-to-date.
	* Login with the account used to install KA Lite
	* Update the Raspberry Pi operating system by:
		* *sudo apt-get update*
		* *sudo apt-get upgrade*
#. Get the installation scripts.
	* *cd /opt*
	* *sudo git clone https://github.com/learningequality/ka-lite-pi-scripts.git*
#. Install and configure the access point.
	* *cd /opt/ka-lite-pi-scripts*
	* *sudo ./configure.sh*
	.. note:: If using the Edimax EW-7811UN, ignore the "hostapdSegmentation fault" error.
#. Install the USB adaptor software.
	* If using the WiPi, run this command:
		* *cd /opt/ka-lite-pi-scripts*
		* *sudo ./use_wipi.sh*
	* If using the Edimax EW-7811Un, run this command:
		* *cd /opt/ka-lite-pi-scripts*
		* *sudo ./use_edimax.sh*
#. Complete the access point configuration
	* *sudo python ./configure_network_interfaces.py*
	* *sudo insserv hostapd*
#. Finally
	* *sudo reboot*
	* A wireless network named "kalite" should be available.
	* Connect to this network
	* If the KA Lite server is started, browse to 1.1.1.1
