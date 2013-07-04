import re
import sys
from cStringIO import StringIO

from django.core.management import call_command
from django.contrib.messages.storage.session import SessionStorage

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

class NoDuplicateMessagesSessionStorage(SessionStorage):
    
    def add(self, level, message, extra_tags=''):
        for m in self._queued_messages:
            if m.level == level and m.message == message:
                return
        super(NoDuplicateMessagesSessionStorage, self).add(level, message, extra_tags)