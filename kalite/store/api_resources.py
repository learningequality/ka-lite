from tastypie import fields
from tastypie.resources import ModelResource, Resource

from django.conf.urls import url

from .models import StoreItem, StoreTransactionLog

from kalite.shared.api_auth.auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource
from django.http.response import Http404


# class StoreItemResource(ModelResource):

#     class Meta:
#         queryset = StoreItem.objects.all()
#         resource_name = 'storeitem'
#         filtering = {
#             "id": ('exact', ),
#             "resource_type": ('exact', ),
#         }


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

    def _read_storeitem(self, storeitem_id, force=False):
        storeitemcache = StoreItem.all(force=force)
        return storeitemcache.get(storeitem_id, None)

    def _read_storeitems(self, storeitem_id=None, force=False):
        storeitemcache = StoreItem.all(force=force)
        return sorted(storeitemcache.values(), key=lambda storeitem: storeitem.cost)

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
            raise Http404('Test with storeitem_id %s not found' % storeitem_id)

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

    class Meta:
        queryset = StoreTransactionLog.objects.all()
        resource_name = 'storetransactionlog'
        filtering = {
            "item": ('exact',),
            "user": ('exact',),
            "reversible": ('exact',),
        }
        authorization = UserObjectsOnlyAuthorization()
