from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.template import loader, Context
from django.utils.timesince import timeuntil
from django.utils.translation import ungettext, ugettext, ugettext_lazy as _
from django.utils.encoding import smart_str

from chronograph.compatibility import dates
from chronograph.settings import LOCK_TIMEOUT

import logging
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback

from datetime import datetime, timedelta
from dateutil import rrule
from StringIO import StringIO
from threading import Thread

logger = logging.getLogger('chronograph.models')

RRULE_WEEKDAY_DICT = {"MO":0,"TU":1,"WE":2,"TH":3,"FR":4,"SA":5,"SU":6}

class JobManager(models.Manager):
    def due(self):
        """
        Returns a ``QuerySet`` of all jobs waiting to be run.  NOTE: this may
        return ``Job``s that are still currently running; it is your
        responsibility to call ``Job.check_is_running()`` to determine whether
        or not the ``Job`` actually needs to be run.
        """
        return self.filter(disabled=False).filter(models.Q(next_run__lte=dates.now()) | models.Q(force_run=True))

# A lot of rrule stuff is from django-schedule
freqs = (
    ("YEARLY", _("Yearly")),
    ("MONTHLY", _("Monthly")),
    ("WEEKLY", _("Weekly")),
    ("DAILY", _("Daily")),
    ("HOURLY", _("Hourly")),
    ("MINUTELY", _("Minutely")),
    ("SECONDLY", _("Secondly"))
)

class JobHeartbeatThread(Thread):
    """
    A very simple thread that updates a temporary "lock" file every second.
    If the ``Job`` that we are associated with gets killed off, then the file
    will no longer be updated and after ``CHRONOGRAPH_LOCK_TIMEOUT`` seconds,
    we assume the ``Job`` has terminated.
    
    The heartbeat should be started with the ``start`` method and once the
    ``Job`` is completed it should be stopped by calling the ``stop`` method.
    """
    daemon = True
    halt = False

    def __init__(self, *args, **kwargs):
        self.lock_file = tempfile.NamedTemporaryFile()
        Thread.__init__(self, *args, **kwargs)

    def run(self):
        """
        Do not call this directly; call ``start()`` instead.
        """
        while not self.halt:
            self.lock_file.seek(0)
            self.lock_file.write(str(time.time()))
            self.lock_file.flush()
            time.sleep(1)
    
    def stop(self):
        """
        Call this to stop the heartbeat.
        """
        self.halt = True
        while self.is_alive():
            time.sleep(.1)
        self.lock_file.close()

class Job(models.Model):
    """
    A recurring ``django-admin`` command to be run.
    """
    name = models.CharField(_("name"), max_length=200)
    frequency = models.CharField(_("frequency"), choices=freqs, max_length=10)
    params = models.TextField(_("params"), null=True, blank=True,
                              help_text=_('Comma-separated list of '
                                          '<a href="http://labix.org/python-dateutil" '
                                          'target="_blank">rrule parameters</a>. '
                                          'e.g: interval:15'))
    command = models.CharField(_("command"), max_length=200, blank=True,
                               help_text=_("A valid django-admin command to "
                                           "run."))
    args = models.CharField(_("args"), max_length=200, blank=True,
        help_text=_("Space separated list; e.g: arg1 option1=True"))
    disabled = models.BooleanField(default=False, help_text=_('If checked this '
                                                              'job will never '
                                                              'run.'))
    next_run = models.DateTimeField(_("next run"), blank=True, null=True,
                                    help_text=_("If you don't set this it will"
                                                " be determined automatically"))
    last_run = models.DateTimeField(_("last run"), editable=False, blank=True,
                                    null=True)
    is_running = models.BooleanField(default=False, editable=False)
    last_run_successful = models.BooleanField(default=True, blank=False,
                                              null=False, editable=False)
    subscribers = models.ManyToManyField(User, blank=True,
                                         limit_choices_to={'is_staff':True})
    lock_file = models.CharField(max_length=255, blank=True, editable=False)
    force_run = models.BooleanField(default=False)
    
    objects = JobManager()
    
    class Meta:
        ordering = ('disabled', 'next_run',)
    
    def __unicode__(self):
        if self.disabled:
            return _(u"%(name)s - disabled") % {'name': self.name}
        return u"%s - %s" % (self.name, self.timeuntil)
    
    def save(self, *args, **kwargs):
        if not self.disabled:
            if self.pk:
                j = Job.objects.get(pk=self.pk)
            else:
                j = self
            if not self.next_run or j.params != self.params:
                logger.debug("Updating 'next_run")
                
                next_run = self.next_run
                if not next_run:
                    next_run = dates.now()
                next_run = dates.make_naive(next_run)
                
                self.next_run = dates.make_aware(self.rrule.after(next_run))
        else:
            self.next_run = None
        
        super(Job, self).save(*args, **kwargs)

    def get_timeuntil(self):
        """
        Returns a string representing the time until the next
        time this Job will be run (actually, the "string" returned
        is really an instance of ``ugettext_lazy``).
        
        >>> from chronograph.compatibility.dates import now
        >>> job = Job(next_run=now())
        >>> job.get_timeuntil().translate('en')
        u'due'
        """
        if self.disabled:
            return _('never (disabled)')
        
        delta = self.next_run - dates.now()
        if delta.days < 0:
            # The job is past due and should be run as soon as possible
            if self.check_is_running():
                return _('running')
            return _('due')
        elif delta.seconds < 60:
            # Adapted from django.utils.timesince
            count = lambda n: ungettext('second', 'seconds', n)
            return ugettext('%(number)d %(type)s') % {'number': delta.seconds,
                                                      'type': count(delta.seconds)}
        return timeuntil(self.next_run)
    get_timeuntil.short_description = _('time until next run')
    timeuntil = property(get_timeuntil)
    
    def get_rrule(self):
        """
        Returns the rrule objects for this ``Job``.  Can also be accessed via the
        ``rrule`` property of the ``Job``.
        
        # Every minute
        >>> last_run = datetime(2011, 8, 4, 7, 19)
        >>> job = Job(frequency="MINUTELY", params="interval:1", last_run=last_run)
        >>> print job.get_rrule().after(last_run)
        2011-08-04 07:20:00
        
        # Every 2 hours
        >>> job = Job(frequency="HOURLY", params="interval:2", last_run=last_run)
        >>> print job.get_rrule().after(last_run)
        2011-08-04 09:19:00
        """
        frequency = eval('rrule.%s' % self.frequency)
        return rrule.rrule(frequency, dtstart=self.last_run, **self.get_params())
    rrule = property(get_rrule)

    def param_to_int(self, param_value):
        """
        Converts a valid rrule parameter to an integer if it is not already one, else
        raises a ``ValueError``.  The following are equivalent:
        
        >>> job = Job(params = "byweekday:1,2,4,5")
        >>> job.get_params()
        {'byweekday': [1, 2, 4, 5]}
        
        >>> job = Job(params = "byweekday:TU,WE,FR,SA")
        >>> job.get_params()
        {'byweekday': [1, 2, 4, 5]}
        """
        if param_value in RRULE_WEEKDAY_DICT:
            return RRULE_WEEKDAY_DICT[param_value]
        try:
            val = int(param_value)
        except ValueError:
            raise ValueError('rrule parameter should be integer or weekday '
                             'constant (e.g. MO, TU, etc.).  '
                             'Error on: %s' % param_value)
        else:
            return val
    
    def get_params(self):
        """
        Converts a string of parameters into a dict.
        
        >>> job = Job(params = "count:1;bysecond:1;byminute:1,2,4,5")
        >>> job.get_params()
        {'count': 1, 'byminute': [1, 2, 4, 5], 'bysecond': 1}
        """
        if self.params is None:
            return {}
        params = self.params.split(';')
        param_dict = []
        for param in params:
            if param.strip() == "":
                continue # skip blanks
            param = param.split(':')
            if len(param) == 2:
                param = (str(param[0]).strip(), [self.param_to_int(p.strip()) for p in param[1].split(',')])
                if len(param[1]) == 1:
                    param = (param[0], param[1][0])
                param_dict.append(param)
        return dict(param_dict)
    
    def get_args(self):
        """
        Processes the args and returns a tuple or (args, options) for passing
        to ``call_command``.
        
        >>> job = Job(args="arg1 arg2 kwarg1='some value'")
        >>> job.get_args()
        (['arg1', 'arg2', "value'"], {'kwarg1': "'some"})
        """
        args = []
        options = {}
        for arg in self.args.split():
            if arg.find('=') > -1:
                key, value = arg.split('=')
                options[smart_str(key)] = smart_str(value)
            else:
                args.append(arg)
        return (args, options)
    
    def is_due(self):
        """
        >>> from chronograph.compatibility.dates import now
        >>> job = Job(next_run=now())
        >>> job.is_due()
        True
        
        >>> job = Job(next_run=now()+timedelta(seconds=60))
        >>> job.is_due()
        False
        
        >>> job.force_run = True
        >>> job.is_due()
        True
        
        >>> job = Job(next_run=now(), disabled=True)
        >>> job.is_due()
        False
        """
        reqs =  (self.next_run <= dates.now() and self.disabled == False 
                and self.check_is_running() == False)
        return (reqs or self.force_run)
    
    def run(self):
        """
        Runs this ``Job``.  A ``Log`` will be created if there is any output
        from either stdout or stderr.
        
        Returns ``True`` if the ``Job`` ran, ``False`` otherwise.
        """
        if not self.disabled:
            if not self.check_is_running() and self.is_due():
                call_command('run_job', str(self.pk))
                return True
        return False
    
    def handle_run(self):
        """
        This method implements the code to actually run a ``Job``.  This is
        meant to be run, primarily, by the `run_job` management command as a
        subprocess, which can be invoked by calling this ``Job``\'s ``run``
        method.
        """     
        args, options = self.get_args()
        stdout = StringIO()
        stderr = StringIO()

        # Redirect output so that we can log it if there is any
        ostdout = sys.stdout
        ostderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stderr
        stdout_str, stderr_str = "", ""

        heartbeat = JobHeartbeatThread()
        run_date = dates.now()
        
        self.is_running = True
        self.lock_file = heartbeat.lock_file.name
        
        self.save()
        
        heartbeat.start()
        try:
            logger.debug("Calling command '%s'" % self.command)
            call_command(self.command, *args, **options)
            logger.debug("Command '%s' completed" % self.command)
            self.last_run_successful = True
        except Exception, e:
            # The command failed to run; log the exception
            t = loader.get_template('chronograph/error_message.txt')
            c = Context({
              'exception': unicode(e),
              'traceback': ['\n'.join(traceback.format_exception(*sys.exc_info()))]
            })
            stderr_str += t.render(c)
            self.last_run_successful = False
        
        # Stop the heartbeat
        logger.debug("Stopping heartbeat")
        heartbeat.stop()
        heartbeat.join()
        
        duration = (dates.now()-run_date).total_seconds()
        
        self.is_running = False
        self.lock_file = ""
        
        # Only care about minute-level resolution
        self.last_run = dates.make_aware(datetime(run_date.year, run_date.month, run_date.day,
                                 run_date.hour, run_date.minute))
        
        # If this was a forced run, then don't update the
        # next_run date
        if self.force_run:
            logger.debug("Resetting 'force_run'")
            self.force_run = False
        else:
            logger.debug("Determining 'next_run'")
            while self.next_run < dates.now():
                self.next_run = dates.make_aware(self.rrule.after(self.next_run))
            logger.debug("'next_run = ' %s" % self.next_run)
        self.save()

        # If we got any output, save it to the log
        stdout_str += stdout.getvalue()
        stderr_str += stderr.getvalue()
        
        if stderr_str:
            # If anything was printed to stderr, consider the run
            # unsuccessful
            self.last_run_successful = False
        
        if stdout_str or stderr_str:
            log = Log.objects.create(
                job = self,
                run_date = run_date,
                stdout = stdout_str,
                stderr = stderr_str,
                success = self.last_run_successful,
                duration = duration
            )

        # Redirect output back to default
        sys.stdout = ostdout
        sys.stderr = ostderr
    
    def check_is_running(self):
        """
        This function actually checks to ensure that a job is running.
        Currently, it only supports `posix` systems.  On non-posix systems
        it returns the value of this job's ``is_running`` field.
        """
        if self.is_running and self.lock_file:
            # The Job thinks that it is running, so lets actually check
            if os.path.exists(self.lock_file):
                # The lock file exists, but if the file hasn't been modified
                # in less than LOCK_TIMEOUT seconds ago, we assume the process
                # is dead
                if (time.time() - os.stat(self.lock_file).st_mtime) <= LOCK_TIMEOUT:
                    return True
            
            # This job isn't running; update it's info
            self.is_running = False
            self.lock_file = ""
            self.save()
        return False
    check_is_running.short_description = "is running"
    check_is_running.boolean = True

class Log(models.Model):
    """
    A record of stdout and stderr of a ``Job``.
    """
    job = models.ForeignKey(Job)
    run_date = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    success = models.BooleanField(default=True, editable=False)
    duration = models.FloatField(editable=False)
        
    class Meta:
        ordering = ('-run_date',)
    
    def __unicode__(self):
        return u"%s - %s" % (self.job.name, self.run_date)
    
    def email_subscribers(self):
            subscribers = []
            for user in self.job.subscribers.all():
                subscribers.append('"%s" <%s>' % (user.get_full_name(), user.email))

            send_mail(
                from_email = '"%s" <%s>' % (settings.EMAIL_SENDER,
                                            settings.EMAIL_HOST_USER),
                subject = '%s' % self,
                recipient_list = subscribers,
                message = "Ouput:\n%s\nError output:\n%s" % (self.stdout, self.stderr)
            )
