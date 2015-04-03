#!/usr/bin/env bash
# Used by vagrant for provisioning

sudo apt-get install -y python2.7 python2.7-dev python-pip
pip install -r requirements.txt
pip install -r dev_requirements.txt
