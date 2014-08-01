from tastypie import fields
from tastypie.resources import ModelResource, Resource

from django.utils.translation import ugettext as _

from .models import StoreItem, StoreTransactionLog

from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource


class StoreItemResource(ModelResource):

    class Meta:
        queryset = StoreItem.objects.all()
        resource_name = 'storeitem'
        filtering = {
            "id": ('exact', ),
            "resource_type": ('exact', ),
        }

class StoreTransactionLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = StoreTransactionLog.objects.all()
        resource_name = 'storetransactionlog'
        filtering = {
            "item": ('exact', ),
            "user": ('exact', ),
            "reversible": ('exact',),
        }
        authorization = UserObjectsOnlyAuthorization()