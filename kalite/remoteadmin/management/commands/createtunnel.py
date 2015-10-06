import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from securesync.models import Device


class Command(BaseCommand):
    help = "Create an SSH tunnel to the SSH server."

    username = "dummy"
    password = "dummy"
    sshport = 6060
    server = "troy.learningequality.org"
    lockfile = os.path.join(tempfile.gettempdir(), 'tunnel.lock')

    option_list = BaseCommand.option_list + tuple()


    def _initial_port_mapping(self, device_id=None):
        if not device_id:
            device_id = Device.get_own_device().id

        return int(device_id[-4:], 16) % (65535 / 2) + (65535 / 2)


    def _check_internet_connection(self):
        print "Checking if we have an internet connection"
        errcount = 0
        while True:
            try:
                socket.create_connection((self.server, self.sshport))
                break
            except socket.error:
                errcount += 1
                if errcount > 5:
                    raise CommandError(_("Can't connect to %(server)s at port %(port)s." % {"server": self.server, "port": self.sshport}))
                else:
                    time.sleep(5)


    def checklockfile(func):
        def checklockfile_wrapper_fn(self, *args, **kwargs):
            if os.path.exists(self.lockfile):
                raise CommandError(_("Another createtunnel command is still running!"))
            else:
                try:
                    with open(self.lockfile, 'w') as f:
                        f.write('lock')
                    func(self, *args, **kwargs)
                except:
                    raise
                finally:
                    if os.path.exists(self.lockfile):
                        os.remove(self.lockfile)
        return checklockfile_wrapper_fn


    def on_exit_delete_lock_file(self):
        def on_exit_callback(*args):
            print "killed ungracefully; deleting lockfile"
            os.remove(self.lockfile)
            sys.exit()
        signals = ["SIGTERM", "SIGKILL", "SIGSTOP", "SIGHUP"]
        for sig in signals:
            signum = getattr(signal, sig)
            try:
                signal.signal(signum, on_exit_callback)
            except:
                print "Skipping handling of %s" % sig


    @checklockfile
    def handle(self, *args, **options):
        remote_port_mapping = self._initial_port_mapping()

        self.on_exit_delete_lock_file()

        # check first if we have an internet connection
        while True:
            self._check_internet_connection()
            print 'trying to open port %s' % remote_port_mapping
            p = subprocess.Popen([
                'ssh',
                '-p', '6060',  # remote ssh port
                "-o", "ExitOnForwardFailure yes",  # exit immediately if we cant forward from the given remote port
                '%s@troy.learningequality.org' % self.username,  # username and host
                '-R', '%s:127.0.0.1:22' % remote_port_mapping,  # remote port to local port mapping
                '-N',  # dont get a remote shell, just establish the remote port forwarding
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            stdout, _stderr = p.communicate()

            if stdout:
                if "remote port forwarding failed for listen port" in stdout:  # remote port already occupied
                    remote_port_mapping += 1
                    continue
                else:
                    raise CommandError(_("Connection refused by %(server)s. Stdout: %(stdout)s" % {"server": self.server, "stdout": stdout}))
