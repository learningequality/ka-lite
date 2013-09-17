from annoying.decorators import render_to

from django.db.models import Sum, Max, Count

from securesync.models import Zone
from shared.decorators import require_authorized_admin


@require_authorized_admin
@render_to("stats/admin_summary_page.html")
def admin_summary_page(request, org_id=None):
    zo = Zone.objects \
        .annotate( \
            last_synced=Max("devicezone__device__client_sessions__timestamp", distinct=True), \
            nsyncsessions=Count("devicezone__device__client_sessions__timestamp", distinct=True), \
            nuploaded=Sum("devicezone__device__client_sessions__models_uploaded", distinct=True), \
            ndevices=Count("devicezone__device", distinct=True), \
        ) \
        .filter(nuploaded__gt=0, devicezone__device__devicemetadata__is_demo_device=False) \
        .order_by("-last_synced") \
        .values(
            "name", "id", "last_synced", "nuploaded", "organization__id", \
            "ndevices", "devicezone__device__name", "devicezone__device__id", "devicezone__device__client_sessions__client_version", "devicezone__device__client_sessions__client_os", \
        )
    return {
        "zones": list(zo[0:20]),
    }
