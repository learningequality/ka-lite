from tastypie import fields
from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from django.http import HttpResponse

import yaml

class NarrativeResource(Resource):

    class Meta:
        resource_name = 'narrative'

    def obj_get_list(self, bundle, **kwargs):
        print bundle.request

        f = open('managetab.yaml')

        narrative_json = yaml.safe_load(f)
        f.close()

        return narrative_json

    # Determines ther desired response format, and serializes the data
    def create_response(self, request, data, response_class=HttpResponse, **response_kwargs):
        response = super(ParentFacilityUserResource, self).create_response(request, data, response_class=response_class, **response_kwargs)
        print response