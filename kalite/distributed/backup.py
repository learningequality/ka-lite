import dbbackup
import datetime
import os
import sys
import time
from os.path import expanduser
from os.path import join

from django.core.management import call_command
from django.conf import settings

from fle_utils.chronograph.models import Job
from fle_utils.chronograph.utils import force_job

DAYS = 7
SECONDS = 86400

def file_rename():
    defaultfilename ='default.backup'
    time = datetime.datetime.now().ctime()
    time = time + '.backup'
    defaultpath = os.path.join(settings.BACKUP_DIRPATH, defaultfilename)
    target = os.path.join(settings.BACKUP_DIRPATH, time)
    if(os.path.exists(defaultpath)):
        os.rename(defaultpath, target)   

def setup_backup():
    command = call_command('kalitebackup')
    force_job("backup",command, frequency="DAILY")

def rotate_backups():
    now = time.time()
    for backupfile in os.listdir(settings.BACKUP_DIRPATH):
        currentFile = os.path.join(settings.BACKUP_DIRPATH, backupfile)
        if os.stat(currentFile).st_mtime < now - DAYS * SECONDS:
            os.remove(currentFile)