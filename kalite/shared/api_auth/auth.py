from django.conf import settings

from tastypie.exceptions import NotFound, Unauthorized
from tastypie.authorization import Authorization, ReadOnlyAuthorization

def _is_central_object_admin(object_list, bundle):
    """Return true if the central server user is allowed to access the objects"""
    user = bundle.request.user
    if not user.is_authenticated():
        return False
    else:
        # check that user can access each object we are returning 
        for obj in object_list:
            # note that this authorization only works for syncable objects
            if not user.get_profile().has_permission_for_object(obj):
                return False
        return True


def _user_is_admin(object_list, bundle):
    """Returns True if and only if the currently logged in user is an admin/teacher."""

    # allow central server superusers to do whatever they want
    if settings.CENTRAL_SERVER and _is_central_object_admin(object_list, bundle):
        return True

    # allow local admins (teachers or administrators) to do anything too
    if getattr(bundle.request, "is_admin", False):
        return True


class UserObjectsOnlyAuthorization(Authorization):

    def _get_user(self, bundle):
        """Convenience method to extract current user from bundle."""

        return bundle.request.session.get("facility_user", None)

    def _user_matches_query(self, bundle):
        """Returns True if and only if the user id in the query is the id of the currently logged in user."""

        user_actual = self._get_user(bundle)

        if not user_actual:
            return False

        user_queried = bundle.request.GET.get("user", None)

        if not user_queried:
            return False

        return user_actual.id == user_queried

    def _all_objects_belong_to_user(self, object_list, bundle):
        """Helper function that checks whether every object "belongs" to current user."""

        user = self._get_user(bundle)

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if obj.user != user:
                return False

        return True

    def read_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        if not self._user_matches_query(bundle):
            raise Unauthorized("Sorry, that information is restricted.")

        return object_list.filter(user=self._get_user(bundle))

    def read_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        return bundle.obj.user == self._get_user(bundle)

    def create_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        if not self._all_objects_belong_to_user(object_list, bundle):
            raise Unauthorized("Sorry, that operation is restricted.")

        return object_list

    def create_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        return bundle.obj.user == self._get_user(bundle)

    def update_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        if not self._all_objects_belong_to_user(object_list, bundle):
            raise Unauthorized("Sorry, that operation is restricted.")

        return object_list

    def update_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        if bundle.obj.user == self._get_user(bundle):
            return True

        raise Unauthorized("Sorry, that operation is restricted.")


    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, that operation is restricted.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, that operation is restricted.")


class AdminReadWriteAndStudentReadOnlyAuthorization(Authorization):

    def _get_user(self, bundle):
        """Convenience method to extract current user from bundle."""

        return bundle.request.session.get("facility_user", None)

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        return []

    def create_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        raise Unauthorized("You are not allowed to access that resource.")

    def update_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        return []

    def update_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        raise Unauthorized("You are not allowed to access that resource.")

    def delete_list(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return object_list

        return []

    def delete_detail(self, object_list, bundle):

        if _user_is_admin(object_list, bundle):
            return True

        raise Unauthorized(_("You are not allowed to access that resource."))


def tastypie_require_admin(handler):

    def tastypie_require_admin_wrapper_fn(self, *args, **kwargs):

        bundle = kwargs.get("bundle")

        # TODO(jamalex): figure out how best to apply this on the central server once needed
        # (possibly using ObjectAdminAuthorization below)
        assert not settings.CENTRAL_SERVER

        if _user_is_admin(bundle):
            return handler(self, *args, **kwargs)

        self.unauthorized_result("You do not have the permissions to access/modify this object.")

    return tastypie_require_admin_wrapper_fn


class ObjectAdminAuthorization(ReadOnlyAuthorization):
    """
    On distributed: Only allow teachers or admins affiliated with the zone
    On central: only allow central server admins affiliated with that zone
    On both: super users do whatever they want
    """

    def _is_central_object_admin(self, object_list, bundle):
        """Return true if the central server user is allowed to access the objects"""
        user = bundle.request.user
        if not user.is_authenticated():
            return False
        else:
            # check that user can access each object we are returning 
            for obj in object_list:
                # note that this authorization only works for syncable objects
                if not user.get_profile().has_permission_for_object(obj):
                    return False
            return True

    def read_list(self, object_list, bundle):
        # On Central
        if settings.CENTRAL_SERVER and self._is_central_object_admin(object_list, bundle):
            return object_list            
        # on distributed
        elif bundle.request.is_admin:
            return object_list
        else:
            raise Unauthorized("Sorry, that operation is restricted.")


    def read_detail(self, object_list, bundle):
        # On Central
        if settings.CENTRAL_SERVER and self._is_central_object_admin(object_list, bundle):
            return True            
        # on distributed
        elif bundle.request.is_admin:
            return True
        else:
            raise Unauthorized("Sorry, that operation is restricted.")
