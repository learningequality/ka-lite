"""
The distributed app represents the KA Lite app itself.  This app connects all of the pieces that
make up the distributed server.  It's largely the app that connects the Khan Academy data and
display with the underlying data structures (topic tree) and data logging, data syncing and
administration, coach reports and data views.

The following apps are imported and used by the distributed app:
* coachreports - for displaying coach reports
* control_panel - for viewing and general server administration
* facility - for user logins and grouping
* i18n - for interacting with language packs (interface translations and dubbed videos)
* main - for defining data (topic tree) and logging of user usage
* securesync - for sharing data between the KA Lite installation and our central data repository
* updates - for dynamic updating of content, resources, and the server software.
"""
import mimetypes
import os
import sys

from django.conf import settings


########################
# Font setup
########################

# Add additional mimetypes to avoid errors/warnings
mimetypes.add_type("font/opentype", ".otf", True)


# set the default encoding
# OK, so why do we reload sys? Because apparently sys.setdefaultencoding
# is deleted somewhere at startup. Reloading brings it back.
# see: http://blog.ianbicking.org/illusive-setdefaultencoding.html
if getattr(settings, "DEFAULT_ENCODING", None):
    reload(sys)
    sys.setdefaultencoding(settings.DEFAULT_ENCODING)
