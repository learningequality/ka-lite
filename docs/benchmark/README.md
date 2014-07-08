## KA-LITE Raspberry Pi benchmark

*Initial version 2 by Gimick*

Provides initial benchmarks for KA-Lite with a Raspberry Pi which is acting as a distributed(Local) server.

Tests and Results are in [TEST_RESULTS.md](/kalite/benchmark/TEST_RESULTS.md)  
Raw data from testing is in [DETAILED_RESULTS.md](/kalite/benchmark/DETAILED_RESULTS.md)

**Hardware** 

* Raspberry Pi 512mb model B, UK board (blue audio jack)
* sandisk 16mb sd card class 4 (blue)
* Realtek RTL8188CUS wifi adaptor TP-LINK model TL-WN725N (this card is not ideal but it is all I have just now - wipi is the recommended adaptor)

**Software**
* Raspbian (debian) fully updated
* Python 2.7.3
* ka-lite (benchmark_v3 branch)


**System setup**

```
#initialise card
sudo dd bs=1M if=put_raspian_image_name-here.img of=/dev/my_sd_card_device_goes_here
```
**Do not** put the wifi adaptor into the Raspberry Pi yet

Raspberry Pi setup is done with a wired internet connection, using ssh to connect.

* Boot the Raspberry Pi

```
sudo raspi-config  --  choose the following options *[Expand Filesystem, Memory Split=16, Update, Hostname]*
```
* Reboot the Raspberry Pi

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python-m2crypto
sudo apt-get install git-core
sudo apt-get autoremove

sudo shutdown -h now
```

* Switch the computer power off
* put the wireless card in
* switch on

```
cd ~
git clone https://github.com/learningequality/ka-lite-pi-scripts.git
cd ka-lite-pi-scripts/
sudo ./configure.sh    #ignore the error "hostapdSegmentation fault"
sudo ./use_edimax.sh
sudo python ./configure_network_interfaces.py
#
sudo insserv hostapd  #needed to start hostapd correctly on reboot
```
To autostart the wireless network on reboot, edit /etc/network/interfaces and add this autostart command:
```
...
auto wlan0
iface wlan0 inet static
...
```
now shutdown

```
sudo shutdown -h now
```

* Switch power off
* wait 10 seconds
* and switch on again

**Install ka-lite**

```
cd ~
git clone https://github.com/gimick/ka-lite.git
cd ka-lite/
git checkout benchmark_v3

#Run the installer, remember to select autostart Y during the install process
./install.sh

sudo reboot
```

**Verify the installation**

* Using a wireless device, attempt to connect to network “kalite”
* From the browser, navigate to 1.1.1.1:8008
* KA-lite home page should be shown

NOTE: On the server, use "ifconfig" to confirm that the wireless device (wlan0) has an IP address.
If it does not have an IP address try adding an "auto wlan0" into /etc/network/interfaces.

**Optimize for performance**

Implement the Raspberry Pi optimizations [PERFORMANCE.md](/kalite/benchmark/PERFORMANCE.md)
