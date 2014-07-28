from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class TeacherOrAdminCanReadWrite(ReadOnlyAuthorization):

    def _raise_unauthorized_if_not_admin(self, bundle):
        if not bundle.request.session.get("is_admin", False):
            raise Unauthorized("You must be logged in as a superuser or teacher to do that!")

    def create_list(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return object_list

    def create_detail(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return True

    def update_list(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return object_list

    def update_detail(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return True

    def delete_list(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return object_list

    def delete_detail(self, object_list, bundle):
        self._raise_unauthorized_if_not_admin(bundle)
        return True
