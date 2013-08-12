from annoying.functions import get_object_or_None
from decorator.decorator import decorator

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseServerError

import kalite
import settings
from central.models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile, FeedListing, Subscription
from securesync.models import Zone
from shared.packaging import package_offline_install_zip
from utils.internet import JsonResponse, return_jsonp


def get_central_server_host(request):
    return request.get_host() or getattr(settings, CENTRAL_SERVER_HOST, "")


def download_kalite_public(request, *args, **kwargs):
    return download_kalite(request, *args, **kwargs)


def download_kalite(request, *args, **kwargs):

    # Parse args
    zone = get_object_or_None(Zone, id=kwargs.get('zone_id', None))
    version = kwargs.get("version", kalite.VERSION)
    platform = kwargs.get("platform", "all")
    locale = kwargs.get("locale", "all")

    # Make sure this user has permission to admin this zone
    if zone and not request.user.is_authenticated():
        raise PermissionDenied("Requires authentication")
    elif zone:
        zone_org = Organization.from_zone(zone)
        if not zone_org or not zone_org[0].id in [org for org in get_or_create_user_profile(request.user).get_organizations()]:
            raise PermissionDenied("Requires authentication")
    
    zip_file = package_offline_install_zip(version=version, platform=platform, locale=locale, zone=zone, central_server=get_central_server_host(request), force=settings.DEBUG)  # force to rebuild zip in debug mode

    # Build the outgoing filename."
    user_facing_filename = "kalite"
    for val in [platform, locale, kalite.VERSION, zone.name if zone else None]:
        user_facing_filename +=  ("-%s" % val) if val not in [None, "", "all"] else ""
    user_facing_filename += ".zip"

    # Stream it back to the user
    zh = open(zip_file,"rb")
    response = HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % user_facing_filename

    return response

@return_jsonp
def get_kalite_version(request):
    return JsonResponse({
        "version": kalite.VERSION,
    })

@return_jsonp
def get_download_urls(request):
    base_url = "%s://%s" % ("https" if request.is_secure() else "http", get_central_server_host(request))

    # TODO: once Dylan makes all subtitle languages available,
    #   don't hard-code this.
    download_sizes = {
        "all": 25.5,
        "en": 19.8,
    }

    downloads = {}
    for locale, size in download_sizes.iteritems():
        urlargs = {
            "version": kalite.VERSION,
            "platform": "all",
            "locale": locale
        }
        downloads[locale] = {
            "display_name": "",  # Will fill in when language list from subtitles is available.
            "size": size,
            "url": "%s%s" % (base_url, reverse("download_kalite_public", kwargs=urlargs)),
        }

    return JsonResponse(downloads)
