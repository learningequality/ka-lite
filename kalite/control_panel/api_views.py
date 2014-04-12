"""
"""
from django.contrib import messages
from django.conf import settings; logging = settings.LOG
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from fle_utils.internet import api_handle_error_with_json, JsonResponseMessageSuccess, JsonResponseMessageError
from kalite.shared.decorators import require_authorized_admin
from securesync.models import Zone


@require_authorized_admin
@api_handle_error_with_json
def delete_zone(request, zone_id):
    zone = get_object_or_404(Zone, id=zone_id)
    if zone.has_dependencies(passable_classes=["Organization"]):
        return JsonResponseMessageError(_("You cannot delete this zone because it is syncing data with with %d device(s)") % zone.devicezone_set.count())
    else:
        zone.delete()
        return JsonResponseMessageSuccess(_("You have successfully deleted %(zone_name)s") % {"zone_name": zone.name})
