import backup

from django.core.management.base import NoArgsCommand

backup_dirpath = expanduser("~")
backup_dirpath = os.path.join(backup_dirpath, 'ka-lite-backups')

class Command(NoArgsCommand):
    help = "Restore backup to a previous state"
    def handle_noargs(self, **options):
        file_list = os.listdir(backup_dirpath) #Retrieve the filenames present in the backup_dirpath
        filelist = []
        filenumber = 0

        for i, f in enumerate(file_list):
            print i, f
            filenumber += 1

        print "Please enter file-number to restore:\n"

        backup_option = int(raw_input())
        if backup_option>=0 and backup_option <=filenumber:
            restoref = filelist[backup_option] #file to be restored based on x
            backup_filepath = os.path.join(backup_dirpath, restoref) #create file path
            call_command('dbrestore', filepath=backup_filepath, database='default') #perform restore
