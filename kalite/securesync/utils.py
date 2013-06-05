from django.core import serializers
from django.db import transaction

from securesync.models import Zone, ZoneKey, ZoneInstallCertificate


json_serializer = serializers.get_serializer("json")()

#                "client_device": json_serializer.serialize([own_device], ensure_ascii=False),
#        return serializers.deserialize("json", r.content)
#

def dump_zone_for_offline_install(zone_id, out_file=None):
    zone = Zone.objects.get(id=zone_id)
    zone_key = ZoneKey.objects.get(zone=zone_id)
    install_certs = ZoneInstallCertificate.objects.filter(zone=zone_id)
    if not install_certs:
        raise Exception("No installation certificates found for zone %s (id=%s)" % (zone.name, zone.id))

    # Remove private key, but only in local object (copy of db)
    #zone_key.private_key = "" # get things working before adding this optimization
    
    # Create the json representation
    objects_json = json_serializer.serialize((zone, zone_key) + tuple(install_certs), ensure_ascii=False)
    if out_file:
        with open(out_file, "w") as fh:  fh.write(objects_json)
    
    return objects_json
    
    
@transaction.commit_on_success
def load_zone_for_offline_install(in_file=None, data=None):
    assert in_file or data, "One parameter must be set."
    
    if not data:
        with open(in_file, "r") as fh:
            data = fh.read()

#    all_models = []
    models = serializers.deserialize("json", data)
    for model in models:
#        all_models.append(model.object)
        model.object.save()
        model.object.full_clean()
