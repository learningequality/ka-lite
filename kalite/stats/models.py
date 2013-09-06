import datetime
from annoying.functions import get_object_or_None

from django.db import models

from securesync.models import ID_MAX_LENGTH, IP_MAX_LENGTH
from settings import LOG as logging


class UnregisteredDevice(models.Model):
    """
    Bare list of all unregistered devices that 'ping' us with a device ID
    """
    id = models.CharField(primary_key=True, max_length=ID_MAX_LENGTH, editable=False)


class UnregisteredDevicePing(models.Model):
    """
    Whenever we receive a session request from an unregistered device,
    we increase our counter
    """
    device = models.ForeignKey("UnregisteredDevice", unique=True)
    npings = models.IntegerField(default=0)
    last_ip = models.CharField(max_length=IP_MAX_LENGTH, blank=True)
    last_ping = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s: %s pings, last on %s from %s" % (self.device.id, self.npings, self.last_ping, self.last_ip)

    @classmethod
    def record_ping(cls, id, ip):
        """
        We received a failed request to create a session; record that 'ping' in our DB
        """
        try:
            # Create the log (if necessary), update, and save
            # TODO: make a base class (in django_utils) that has get_or_initialize, and use that
            #   to shorten things here
            cur_log = get_object_or_None(cls, device__id=id)  # get is safe, because device is unique
            if not cur_log:
                (cur_device, _) = UnregisteredDevice.objects.get_or_create(id=id)
                cur_log = cls(device=cur_device)

            cur_log.npings += 1
            cur_log.last_ip = ip
            cur_log.save()

        except Exception as e:
            # Never block functionality
            logging.debug(e)