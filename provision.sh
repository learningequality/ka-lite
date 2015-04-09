#!/usr/bin/env bash
# Used by vagrant for provisioning

apt-get install -y python2.7 python2.7-dev python-pip
pip install -r /home/vagrant/ka-lite/requirements.txt
pip install -r /home/vagrant/ka-lite/dev_requirements.txt
