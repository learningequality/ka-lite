from collections import defaultdict
from optparse import make_option
import logging
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.admindocs.views import extract_views_from_urlpatterns

from crawler.base import Crawler

class LogStatsHandler(logging.Handler):
    stats = defaultdict(int)

    def emit(self, record):
        self.stats[record.levelno] += 1

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-b', '--pdb', action='store_true', dest='pdb', default=False,
            help='Pass -b to drop into pdb on an error'),
        make_option('-d', '--depth', action='store', dest='depth', default=3,
            help='Specify the depth to crawl.'),
        make_option('-s', '--safe', action='store_true', dest='html', default=False,
            help='Pass -s to check for html fragments in your pages.'),
        make_option('-r', '--response', action='store_true', dest='response', default=False,
            help='Pass -r to store the response objects.'),
        make_option('-t', '--time', action='store_true', dest='time', default=False,
            help='Pass -t to time your requests.'),
        make_option('--enable-plugin', action='append', dest='plugins', default=[],
            help='Enable the specified plugin'),
        make_option("-o", '--output-dir', action='store', dest='output_dir', default=None,
            help='If specified, store plugin output in the provided directory'),
        make_option('--no-parent', action='store_true', dest="no_parent", default=False,
            help='Do not crawl URLs which do not start with your base URL'),
        make_option('-u', "--auth", action='store', dest='auth', default=None,
            help='Authenticate (login:user,password:secret) before crawl'),
            
        # INFO(bcipolli): added for django (and changed url options above to accommodate)
        make_option('-a', "--remote-addr", action='store', dest='remote_addr', default="127.0.0.1",
            help='Remote address (hostname); default=localhost (127.0.0.1)'),
        make_option('-p', "--remote-port", action='store', dest='remote_port', default="8008",
            help='Remote port; default=8008'),
    )

    help = "Displays all of the url matching routes for the project."
    args = "[relative start url]"

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        depth = int(options.get('depth', 3))

        auth = _parse_auth(options.get('auth'))

        if verbosity == 3:
            log_level = 1
        elif verbosity == 2:
            log_level = logging.DEBUG
        elif verbosity:
            log_level = logging.INFO
        else:
            log_level = logging.WARN

        crawl_logger = logging.getLogger('crawler')
        crawl_logger.setLevel(logging.DEBUG)
        crawl_logger.propagate = 0

        log_stats = LogStatsHandler()

        crawl_logger.addHandler(log_stats)

        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(logging.Formatter("%(name)s [%(levelname)s] %(module)s: %(message)s"))

        crawl_logger.addHandler(console)

        if len(args) > 1:
            raise CommandError('Only one start url is currently supported.')
        else:
            start_url = args[0] if args else '/'

        if settings.ADMIN_FOR:
            settings_modules = [__import__(m, {}, {}, ['']) for m in settings.ADMIN_FOR]
        else:
            settings_modules = [settings]

        conf_urls = {}

        # Build the list URLs to test from urlpatterns:
        for settings_mod in settings_modules:
            try:
                urlconf = __import__(settings_mod.ROOT_URLCONF, {}, {}, [''])
            except Exception, e:
                logging.exception("Error occurred while trying to load %s: %s", settings_mod.ROOT_URLCONF, str(e))
                continue

            view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
            for (func, regex) in view_functions:
                #Get function name and add it to the hash of URLConf urls
                func_name = hasattr(func, '__name__') and func.__name__ or repr(func)
                conf_urls[regex] = ['func.__module__', func_name]

        c = Crawler(start_url,
            conf_urls=conf_urls,
            verbosity=verbosity,
            output_dir=options.get("output_dir"),
            ascend=not options.get("no_parent"),
            auth=auth,
            remote_addr=options.get("remote_addr"),
            remote_port=options.get("remote_port"),
        )

        # Load plugins:
        for p in options['plugins']:
            crawl_logger.debug("Enabling plugin %s" % p)
             
            # This nested try is somewhat unsightly but allows easy Pythonic
            # usage ("--enable-plugin=tidy") instead of Java-esque
            # "--enable-plugin=crawler.plugins.tidy"
            try:
                try:
                    plugin_module = __import__(p)
                except ImportError:
                    if not "." in p:
                        plugin_module = __import__(
                            "crawler.plugins.%s" % p,
                            fromlist=["crawler.plugins"]
                        )
                    else:
                        raise

                c.plugins.append(plugin_module.PLUGIN())
            except (ImportError, AttributeError), e:
                crawl_logger.critical("Unable to load plugin %s: %s", p, e)
                sys.exit(3)

        c.run(max_depth=depth)

        # We'll exit with a non-zero status if we had any errors
        max_log_level = max(log_stats.stats.keys())
        if max_log_level >= logging.ERROR:
            sys.exit(2)
        elif max_log_level >= logging.WARNING:
            sys.exit(1)
        else:
            sys.exit(0)


def _parse_auth(auth):
    """
    Parse auth string and return dict.

    >>> _parse_auth('login:user,password:secret')
    {'login': 'user', 'password': 'secret'}

    >>> _parse_auth('name:user, token:top:secret')
    {'name': 'user', 'token': 'top:secret'}
    """
    if not auth:
        return None
    items = auth.split(',')
    return dict(i.strip().split(':', 1) for i in items)
