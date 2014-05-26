from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class FacilityUserCanWriteAuthorization(ReadOnlyAuthorization):
    def get_user_or_raise_unauthorized(self, bundle):
        user = bundle.request.session.get('facility_user')
        if not user:
            return user
        else:
            raise Unauthorized("Only facility user allowed")

    def create_list(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list

    def create_detail(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list

    def update_list(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list

    def update_detail(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list

    def delete_list(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list

    def delete_detail(self, object_list, bundle):
        self.get_user_or_raise_unauthorized(bundle)
        return object_list
