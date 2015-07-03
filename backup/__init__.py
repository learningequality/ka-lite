import dbbackup

from django.core.management import call_command

from fle_utils.chronograph.models import Job

def setup_backup():
	try:
		command = call_command('dbbackup')
		schedule_job(command, frequency="DAILY")
	except:
		#Catch the KeyError exception
		pass

setup_backup()
