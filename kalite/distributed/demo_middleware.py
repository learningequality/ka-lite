"""
This middle-ware should be included for any online demo of KA Lite.
It does things like:
* Informs the user about the admin login
* Links to documentation on how to use KA Lite
* Prevents certain sensitive resources from being accessed (like the admin interface)
"""
import re

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


def is_static_file(path):

    url_exceptions = [
        "^/admin/*",
        "^/api/*",
        "^/securesync/api/*",
        "^{url}/*".format(url=settings.STATIC_URL),
        "^/data/*",
        "^{url}/*".format(url=settings.MEDIA_URL),
        "^/handlebars/*",
        "^.*/_generated/*"
    ]

    for item in url_exceptions:
        p = re.compile(item)
        if p.match(path):
            return True

    return False


class LinkUserManual:
    """Shows a message with a link to the user's manual, from the homepage."""
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if request.path == reverse("homepage"):
            messages.info(request, mark_safe(_("Welcome to our demo server!"
                "  Please visit our <a href='%(um_url)s'>user's manual</a> or <a href='%(home_url)s'>homepage</a> for more information.") % {
                    "um_url": "https://learningequality.org/docs/usermanual/userman_main.html",
                    "home_url": "https://learningequality.org/ka-lite/",
            }))

class ShowAdminLogin:
    """Shows a message with the admin username/password"""
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if not request.is_logged_in:
            messages.info(request, mark_safe(_("<a href='%(sign_up_url)s'>Sign up as a learner</a>, or log in as the site-wide admin (username=%(user_name)s, password=%(passwd)s)" % {
                "sign_up_url": reverse("facility_user_signup"),
                "user_name": settings.DEMO_ADMIN_USERNAME,
                "passwd": settings.DEMO_ADMIN_PASSWORD,
            })))

class StopAdminAccess:
    """Prevents access to the Django admin"""
    def process_request(self, request):
        if request.path.startswith(reverse("admin:index")):
            msg = _("The admin interface is disabled in the demo server.")
            messages.error(request, msg)
            raise PermissionDenied(msg)
