#!/usr/bin/env bash
# Used by vagrant for provisioning

apt-get install -y python2.7 python2.7-dev python-pip
python /home/vagrant/ka-lite/kalite/manage.py contentload -i /home/vagrant/ka-lite/tablet-content/ -c connectteaching --traceback
