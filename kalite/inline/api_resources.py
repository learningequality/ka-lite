from tastypie import fields
from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from django.http import HttpResponse

import yaml
import os

class NarrativeResource(Resource):
    intro = fields.CharField(attribute='intro')
    class Meta:
        resource_name = 'narrative'

    # fetches an individual object on the resource, based on id
    # raises a NotFound exception
    def detail_uri_kwargs(self, bundle_or_obj):
        print "this is our kwargs insdie detali"
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.intro
        else:
            kwargs['pk'] = bundle_or_obj.intro

        return kwargs

    def obj_get(self, bundle, **kwargs):
        print "-------------------------------------"
        
        try:
            print "inside try block"
            f = open("kalite/inline/managetab.yaml", 'r')
            narrative_json = yaml.safe_load(f)
            f.close()
            return narrative_json
        except KeyError:
            raise NotFound("Narrative not found.")

        print "we made it out alive"
