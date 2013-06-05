from models import Zone, ZoneKey

from django.core import serializers


json_serializer = serializers.get_serializer("json")()

#                "client_device": json_serializer.serialize([own_device], ensure_ascii=False),
#        return serializers.deserialize("json", r.content)
#

def dump_zone_for_offline_install(zone_name, out_file=None):
    zone = Zone.objects.get(name=zone_name)
    zone_key = zone.zone_key
    
    objects_json = json_serializer.serialize([zone, zone_key], ensure_ascii=False)
    
    if out_file:
        with open(out_file, "w") as fh:
            fh.write(objects_json)
    
    return objects_json
    
    
def load_zone_for_offline_install(in_file=None, data=None):
    assert in_file or data, "One parameter must be set."
    
    if not data:
        with open(in_file, "r") as fh:
            data = fh.read()

    models = serializers.deserialize("json", data)
    for model in models:
        model.full_clean()
        model.save()