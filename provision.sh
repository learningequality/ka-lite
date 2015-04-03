#!/usr/bin/env bash
# Used by vagrant for provisioning

sudo apt-get install -y python2.7 python2.7-dev
pip install -r /kalite/requirements.txt
pip install -r /kalite/dev_requirements.txt
