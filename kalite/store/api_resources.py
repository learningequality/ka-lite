from tastypie import fields
from tastypie.resources import ModelResource, Resource

from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from .models import StoreTransactionLog
from .data.items import STORE_ITEMS

from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource


# class StoreItemResource(ModelResource):

#     class Meta:
#         queryset = StoreItem.objects.all()
#         resource_name = 'storeitem'
#         filtering = {
#             "id": ('exact', ),
#             "resource_type": ('exact', ),
#         }

storeitemcache = {}


class StoreItem():
    def __init__(self, **kwargs):
        storeitem_id = kwargs.get('storeitem_id')
        self.storeitem_id = storeitem_id
        self.cost = kwargs.get("cost", None)
        self.returnable = kwargs.get("returnable", None)
        self.title = kwargs.get("title", None)
        self.description = kwargs.get("description", None)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.resource_id = kwargs.get("resource_id", None)
        self.resource_type = kwargs.get("resource_type", None)
        self.shown = kwargs.get("shown", True)


class StoreItemResource(Resource):

    cost = fields.IntegerField(attribute="cost", null=True)
    returnable = fields.BooleanField(attribute="returnable", default=False)
    title = fields.CharField(attribute="title")
    description = fields.CharField(attribute="description")
    thumbnail = fields.CharField(attribute="thumbnail", null=True)
    resource_id = fields.CharField(attribute="resource_id", null=True)
    resource_type = fields.CharField(attribute="resource_type", null=True)
    shown = fields.BooleanField(attribute="shown", default=True)

    class Meta:
        resource_name = 'storeitem'
        object_class = StoreItem

    #TODO(aron): refactor reading of storeitems json files
    def _refresh_storeitems_cache(self):
        for key, value in STORE_ITEMS.items():
            # Coerce each storeitem dict into a StoreItem object
            value["storeitem_id"] = key
            storeitemcache[key] = (StoreItem(**value))

    def _read_storeitem(self, storeitem_id, force=False):
        if not storeitemcache or force:
            self._refresh_storeitems_cache()
        return storeitemcache.get(storeitem_id, None)

    def _read_storeitems(self, storeitem_id=None, force=False):
        if not storeitemcache or force:
            self._refresh_storeitems_cache()
        return sorted(storeitemcache.values(), key=lambda storeitem: storeitem.title)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<storeitem_id>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.storeitem_id
        else:
            kwargs['pk'] = bundle_or_obj.storeitem_id
        return kwargs

    def get_object_list(self, request, force=False):
        """
        Get the list of storeitems based from a request.
        """
        return self._read_storeitems(force=force)

    def obj_get_list(self, bundle, **kwargs):
        force = bundle.request.GET.get('force', False)
        return self.get_object_list(bundle.request, force=force)

    def obj_get(self, bundle, **kwargs):
        # logging.warn('==> API get %s -- %s' % (bundle.request.user, bundle.request.is_teacher,))
        storeitem_id = kwargs.get("storeitem_id", None)
        storeitem = self._read_storeitem(storeitem_id)
        if storeitem:
            return storeitem
        else:
            raise NotFound('Test with storeitem_id %s not found' % storeitem_id)

    def obj_create(self, request):
        # logging.warn('==> API create %s -- %s' % (request.user, request.is_teacher,))
        raise NotImplemented("Operation not implemented yet for storeitems.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for storeitems.")

    def obj_delete_list(self, request):
        # logging.warn('==> API delete_list %s' % request.user)
        raise NotImplemented("Operation not implemented yet for storeitems.")

    def obj_delete(self, request):
        # logging.warn('==> API delete %s' % request.user)
        raise NotImplemented("Operation not implemented yet for storeitems.")

    def rollback(self, request):
        # logging.warn('==> API rollback %s' % request.user)
        raise NotImplemented("Operation not implemented yet for storeitems.")



class StoreTransactionLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')
    item = fields.ForeignKey(StoreItemResource, 'item')

    class Meta:
        queryset = StoreTransactionLog.objects.all()
        resource_name = 'storetransactionlog'
        filtering = {
            "item": ('exact', ),
            "user": ('exact', ),
            "reversible": ('exact',),
        }
        authorization = UserObjectsOnlyAuthorization()