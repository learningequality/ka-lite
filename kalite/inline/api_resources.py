from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from django.http import HttpResponse

import yaml
import os


# initial = some object
# 'intro' - the attribute
class NarrativeObj():
    def __init__(self, req=None):
        if not req:
            return

        print "INITIALIZING NARROBJ"

        f = open("kalite/inline/narratives.yaml", 'r')
        narrative_json = yaml.safe_load(f)
        f.close()

        self.intro = narrative_json[req]
        print self.__dict__['intro']

class NarrativeResource(Resource):
    intro = fields.CharField(attribute='intro')
    id =
    class Meta:
        resource_name = 'narrative'
        object_class = NarrativeObj

    # fetches an individual object on the resource, based on id
    # raises a NotFound exception
    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, NarrativeObj):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id

        return kwargs

    def obj_get(self, bundle, **kwargs):
        print "\n----------------------------------------------"
        request = kwargs['pk']

        try:
            nobj = NarrativeObj(request)
            return nobj
        except Exception as e:
            raise NotFound("Narrative not found.")

        print "we made it out alive"
