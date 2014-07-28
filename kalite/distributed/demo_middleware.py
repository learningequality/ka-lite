"""
This middle-ware should be included for any online demo of KA Lite.
It does things like:
* Informs the user about the admin login
* Links to documentation on how to use KA Lite
* Prevents certain sensitive resources from being accessed (like the admin interface)
"""
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


def is_static_file(path):
    return path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL)

class LinkUserManual:
    """Shows a message with a link to the user's manual, from the homepage."""
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if request.path == reverse("homepage"):
            messages.info(request, mark_safe(_("Welcome to our demo server!"
                "  Please visit our <a href='%(um_url)s'>user's manual</a> or <a href='%(home_url)s'>homepage</a> for more information.") % {
                    "um_url": "http://kalitewiki.learningequality.org/user-s-manual/using-ka-lite",
                    "home_url": "http://kalite.learningequality.org/",
            }))

class ShowAdminLogin:
    """Shows a message with the admin username/password"""
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if not request.is_logged_in:
            messages.info(request, mark_safe(_("<a href='%(sign_up_url)s'>Sign up as a student</a>, or <a href='%(log_in_url)s'>log in</a> as the site-wide admin (username=%(user_name)s, password=%(passwd)s)" % {
                "sign_up_url": reverse("facility_user_signup"),
                "log_in_url": reverse("login"),
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