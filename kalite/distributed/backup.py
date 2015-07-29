import dbbackup
import datetime
import os
import sys
import time
from os.path import expanduser
from django.core.management import call_command

from fle_utils.chronograph.models import Job

backup_dirpath = expanduser("~")
backup_dirpath = os.path.join(backup_dirpath, 'ka-lite-backups')

def file_rename():
    filename ='default.backup'
    time = datetime.datetime.now().ctime()
    path = os.path.join(backup_dirpath, filename)
    target = os.path.join(backup_dirpath, time + '.backup')

    if path.exists():
        os.rename(path, target)

def setup_backup():
    try:
        command = call_command('dbbackup')
        force_job(command, frequency="DAILY")
    except KeyError:
        pass

def rotate_backups():
    now = time.time()
    for fp in os.listdir(backup_dirpath):
        if os.stat(os.path.join(backup_dirpath, fp)).st_mtime < now - 7 * 86400:
            os.remove(os.path.join(backup_dirpath, fp))