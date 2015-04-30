from django.db import models
from django.http import HttpResponse

from tastypie import fields
from tastypie.resources import ModelResource

import yaml

class NarrativeResource(Resource):
# Just like a Django ``Form`` or ``Model``, we're defining all the
    # fields we're going to handle with the API here.
    #uuid = fields.CharField(attribute='uuid')
    #user_uuid = fields.CharField(attribute='user_uuid')
    #message = fields.CharField(attribute='message')
    #created = fields.IntegerField(attribute='created')
    
    class Meta:
        resource_name = 'narrative'

    # Fetches an individual object, this is called when
    # the URL endpoint is matched
    def obj_get(self, bundle, **kwargs):
        print bundle.request
        
        narr_yaml = open('managetab.yaml')
        narr_obj = yaml.safe_load(narr_yaml)
        narr_yaml.close()

        return narr_obj


