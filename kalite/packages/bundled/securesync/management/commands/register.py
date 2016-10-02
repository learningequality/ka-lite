from optparse import make_option
import requests
import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from ...devices.api_client import RegistrationClient
from ...models import Device, DeviceZone, Zone

class Command(BaseCommand):
    help = "Register this device with the central server."

    option_list = BaseCommand.option_list + (
        # Basic options
        # Functional options
        make_option('-u', '--username',
            action='store',
            dest='username',
            default="centraladmin",
            help='Central server username/email'),

        make_option('-p', '--password',
            action='store',
            dest='password',
            default="centraladmin",
            help='Central server password'),

        make_option('-z', '--zone',
            action='store',
            dest='zone',
            default=None,
            help='ID of the zone to register onto'),

    )

    def handle(self, *args, **options):

        # ensure we have a local device
        assert Device.get_own_device() is not None, "No local device exists!"

        # ensure we're not already registered
        assert not Device.get_own_device().is_registered(), "Device has already been registered!"

        # get a registration client to talk to the central server reg API
        client = RegistrationClient()

        # check connection to central server
        assert client.test_connection() == "success", "Unable to connect to the central server!"

        # ensure a zone was specified
        assert options.get("zone", None), "You must specify a zone."

        # simulate browser-based reg process
        s = requests.session()

        # login to the central server
        login_url = client.path_to_url("/accounts/login/")
        r = s.get(login_url)
        csrftoken = s.cookies['csrftoken_central']
        login_data = dict(username=options["username"], password=options["password"], csrfmiddlewaretoken=csrftoken, next='/')
        r = s.post(login_url, data=login_data, headers={"Referer": login_url})
        assert r.status_code == 200, "Error logging into central server: " + r.content

        # register on the central server
        reg_url = client.get_registration_url()
        r = s.get(reg_url)
        assert options["zone"] in r.content, "Zone does not seem to exist under your central server account."
        csrftoken = s.cookies['csrftoken_central']
        reg_data = dict(zone=options["zone"], public_key=Device.get_own_device().public_key, csrfmiddlewaretoken=csrftoken)
        r = s.post(reg_url, data=reg_data, headers={"Referer": reg_url})
        assert r.status_code == 200, "Error registering public key with central server: %s" % r.content

        # trigger local post-reg background reg finalization
        result = client.register()
        assert result.get("code") == "registered", "Error doing background registration finalization: %s" % result

        # wrap up and confirm!
        own_device = Device.get_own_device()
        assert own_device.is_registered(), "Device was not registered successfully..."
        sys.stdout.write("Device '%s' has been successfully registered to zone '%s'!\n" % (own_device.id, own_device.get_zone().id))


