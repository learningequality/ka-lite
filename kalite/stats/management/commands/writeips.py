from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import SyncSession


class Command(BaseCommand):
    help = "Generate IP address list."

    option_list = BaseCommand.option_list + (
        make_option('-f', '--file',
                    action='store',
                    dest='file',
                    default="ips.txt",
                    metavar="FILE",
                    help="Output filename"),
        )

    def handle(self, *args, **options):
        f = open(options["file"], "w")
        ips = [addr.strip() for ip in SyncSession.objects.values("ip").distinct() for addr in ip["ip"].split(",")]
        ips = list(set(ips) - set([""]))
        ips = sorted(ips)  # easier for human-readable reviewing for any issues

        f.write("\n".join(ips))
        f.close()