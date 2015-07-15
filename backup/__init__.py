import dbbackup
import datetime
import os
import sys
import time

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
	except KeyError

def restore_list():
    file_list = os.listdir(backup_dirpath) #Retrieve the filenames present in the backup_dirpath
    filelist = [] 
    filenumber = 0 
    
    for eachfile in file_list:
        filelist.append(eachfile) #Store files one by one
        print filelist.index(eachfile), eachfile #show file number: index
        filenumber += 1 
    
    print "Please enter file-number to restore:\n"
    
    backup_option = int(raw_input())
    restoref = filelist[backup_option] #file to be restored based on x
    backup_filepath = os.path.join(backup_dirpath, restoref) #create file path
    call_command('dbrestore', filepath=backup_filepath, database='default') #perform restore

def rotate_backups():
    now = time.time()
    print backup_dirpath
    for fp in os.listdir(backup_dirpath):
        if os.stat(os.path.join(backup_dirpath, fp)).st_mtime < now - 7 * 86400:
            os.remove(os.path.join(backup_dirpath, fp))

setup_backup()
