#!/usr/bin/env bash
# Used by vagrant for provisioning

apt-get update
apt-get install -y python2.7 python2.7-dev python-pip
curl -sL https://deb.nodesource.com/setup | bash -
apt-get install -y nodejs
pip install -r /home/vagrant/ka-lite/requirements.txt
pip install -r /home/vagrant/ka-lite/dev_requirements.txt
cd /home/vagrant/ka-lite
# --no-bin-links option is for linux guests on windows hosts
npm install --no-bin-links
