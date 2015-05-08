from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from django.http import HttpResponse

import yaml

class NarrativeResource(Resource):

    class Meta:
        resource_name = 'narrative'

    # fetches the list of objets available on the resource
    def obj_get_list(self, bundle, **kwargs):
        print "hello"

        # f = open('managetab.yaml')

        # narrative_json = yaml.safe_load(f)
        # f.close()

        # return narrative_json

    # fetches an individual object on the resource, based on id
    # raises a NotFound exception
    def obj_get(self, bundle, **kwargs):
        # print bundle.request
        f = open('managetab.yaml')
        narrative_json = yaml.safe_load(f)
        f.close()
        return narrative_json

    def urls(self):
       return '/inline/management/zone/None';