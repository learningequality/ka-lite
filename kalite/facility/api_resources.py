import datetime
import os
from dateutil.tz import tzlocal

from tastypie import fields
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash

from .api_authorizations import TeacherOrAdminCanReadWrite
from .models import Facility, FacilityGroup, FacilityUser

from django.conf import settings; logging = settings.LOG
from django.conf.urls import url
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie

from kalite import version
from kalite.i18n import lcode_to_django_lang
from kalite.distributed.api_views import compute_total_points, get_messages_for_api_calls
from kalite.main.models import UserLog

from securesync.models import Device


class FacilityResource(ModelResource):
    class Meta:
        queryset = Facility.objects.all()
        resource_name = 'facility'
        authorization = TeacherOrAdminCanReadWrite()

class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        authorization = TeacherOrAdminCanReadWrite()


class FacilityUserResource(ModelResource):
    facility = fields.ForeignKey(FacilityResource, 'facility')

    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'user'
        authorization = TeacherOrAdminCanReadWrite()
        filtering = {
            'facility': ALL_WITH_RELATIONS,
            'is_teacher': ['exact']
        }
        exclude = ["password"]

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/login%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('login'), name="api_login"),
            url(r'^(?P<resource_name>%s)/logout%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('logout'), name='api_logout'),
            url(r'^(?P<resource_name>%s)/status%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('status'), name='api_status'),
        ]

    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        logout(request)

        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')
        facility = data.get('facility', '')

        # first try logging in as a Django user
        if not settings.CENTRAL_SERVER:
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return self.create_response(request, {
                    'success': True,
                    'redirect': reverse("zone_redirect")
                    })

        # Find all matching users
        users = FacilityUser.objects.filter(username=username, facility=facility)

        if users.count() == 0:
            if Facility.objects.count() > 1:
                error_message = _("Username was not found for this facility. Did you type your username correctly, and choose the right facility?")
            else:
                error_message = _("Username was not found. Did you type your username correctly?")
            return self.create_response(request, {
                'messages': {'error': error_message},
                'error_highlight': "username"
                }, HttpUnauthorized )

        for user in users:
            if settings.SIMPLIFIED_LOGIN and not user.is_teacher:
                # For simplified login, as long as it is a student account just take the first one!
                break
            # if we find a user whose password matches, stop looking
            if user.check_password(password):
                break
            else:
                user = None

        if not user:
            return self.create_response(request, {
                'messages': {'error': _("Password was incorrect. Please try again.")},
                # Specify which field to highlight as in error.
                'error_highlight': "password"
                }, HttpUnauthorized )
        else:
            try:
                UserLog.begin_user_activity(user, activity_type="login", language=lcode_to_django_lang(request.language))  # Success! Log the event (ignoring validation failures)
            except ValidationError as e:
                logging.error("Failed to begin_user_activity upon login: %s" % e)

            request.session["facility_user"] = user
            messages.success(request, _("You've been logged in! We hope you enjoy your time with KA Lite ")
                + _("-- be sure to log out when you finish."))

            extras = {'success': True}
            if user.is_teacher:
                extras.update({
                    "redirect": reverse("coach_reports", kwargs={"zone_id": getattr(Device.get_own_device().get_zone(), "id", "None")})
                })
            return self.create_response(request, extras)


    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        logout(request)
        return self.create_response(request, {
            'success': True,
            'redirect': reverse("homepage")
            })

    def status(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        """In order to promote (efficient) caching on (low-powered)
        distributed devices, we do not include ANY user data in our
        templates.  Instead, an AJAX request is made to download user
        data, and javascript used to update the page.

        This view is the view providing the json blob of user information,
        for each page view on the distributed server.

        Besides basic user data, we also provide access to the
        Django message system through this API, again to promote
        caching by excluding any dynamic information from the server-generated
        templates.
        """
        @ensure_csrf_cookie
        def add_csrf(request):
            return request

        request = add_csrf(request)

        return self.create_response(request, self.generate_status(request))


    def generate_status(self, request, **kwargs):
        #Build a list of messages to pass to the user.
        #   Iterating over the messages removes them from the
        #   session storage, thus they only appear once.

        message_dicts = get_messages_for_api_calls(request)

        # Default data
        data = {
            "is_logged_in": request.is_logged_in,
            "registered": request.session.get("registered", True),
            "is_admin": request.is_admin,
            "is_django_user": request.is_django_user,
            "points": 0,
            "current_language": request.session.get(settings.LANGUAGE_COOKIE_NAME),
            "messages": message_dicts,
            "status_timestamp": datetime.datetime.now(tzlocal()),
            "version": version.VERSION,
            "facilities": request.session.get("facilities"),
            "simplified_login": settings.SIMPLIFIED_LOGIN,
            "docs_exist": getattr(settings, "DOCS_EXIST", False),
            "zone_id": getattr(Device.get_own_device().get_zone(), "id", "None"),
            "has_superuser": User.objects.filter(is_superuser=True).exists(),
        }

        # Override properties using facility data
        if "facility_user" in request.session:  # Facility user
            user = request.session["facility_user"]
            data["is_logged_in"] = True
            data["username"] = user.get_name()
            # TODO-BLOCKER(jamalex): re-enable this conditional once tastypie endpoints invalidate cached session value
            # if "points" not in request.session:
            request.session["points"] = compute_total_points(user)
            data["points"] = request.session["points"] if request.session["points"] else 0
            data["user_id"] = user.id
            data["user_uri"] = reverse("api_dispatch_detail", kwargs={"resource_name": "user", "pk": user.id})
            data["facility_id"] = user.facility.id

        # Override data using django data
        if request.user.is_authenticated():  # Django user
            data["is_logged_in"] = True
            data["username"] = request.user.username

        return data

