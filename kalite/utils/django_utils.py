import os
import re
import subprocess
import sys
from cStringIO import StringIO

from django.core.management import call_command
from django.contrib.messages.storage.session import SessionStorage

import settings


def call_command_with_output(cmd, *args, **kwargs): 
    """Run call_command while capturing stdout/stderr and calls to sys.exit"""
    
    backups = [sys.stdout, sys.stderr, sys.exit]
    try:
        sys.stdout = StringIO()     # capture output
        sys.stderr = StringIO()
        sys.exit = lambda exit_code: sys.stderr.write("Exit code: %d" % exit_code) if exit_code else ""

        call_command(cmd, *args, **kwargs)

        out = sys.stdout.getvalue() # release output
        err = sys.stderr.getvalue() # release err
        
        # parse off exit code from stderr
        match = re.match(r".*Exit code: ([0-9]+)$", err.replace("\n",""), re.M)
        if match is None:
            val = 0
        else:
            val = int(match.groups()[0])
            
            # Having trouble regexp-ing with newlines :(  Here's my hacky solution
            match = re.match(r"^(.*)__newline__Exit code: [0-9]+$", err.replace("\n", "__newline__"), re.M)
            assert match is not None
            err = match.groups()[0].replace("__newline__", "\n")

        return (out,err, val)
        
    finally:
        sys.stdout = backups[0]
        sys.stderr = backups[1]
        sys.exit   = backups[2]


def call_command_async(cmd, *args, **kwargs):
    """
    This may be finicky, as it requires stringifying.
    """
    # Use sys to get the same executable running as is running this process.
    # Make sure to call the manage.py from this project.
    call_args = [sys.executable, os.path.join(settings.PROJECT_PATH, "manage.py"), cmd]
    call_args += list(args)
    for key,val in kwargs:
        call_args.append("--%s=%s", key, val)

    import pdb; pdb.set_trace()
    subprocess.Popen(call_args)


class NoDuplicateMessagesSessionStorage(SessionStorage):
    """
    This storage class prevents any messages from being added to the message buffer
    more than once.

    We extend the session store for AJAX-based messaging to work in Django 1.4,
       due to this bug: https://code.djangoproject.com/ticket/19387
    """

    def add(self, level, message, extra_tags=''):
        for m in self._queued_messages:
            if m.level == level and m.message == message and m.extra_tags == extra_tags:
                return
        super(NoDuplicateMessagesSessionStorage, self).add(level, message, extra_tags)