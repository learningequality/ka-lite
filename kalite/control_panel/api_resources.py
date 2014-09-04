from annoying.functions import get_object_or_None
from tastypie.exceptions import NotFound, BadRequest
from tastypie.resources import Resource, ModelResource
from tastypie.serializers import Serializer

from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.shared.api_auth import ObjectAdminAuthorization
from securesync.models import Zone


class FacilityResource(ModelResource):
    class Meta:
        queryset = Facility.objects.all()
        resource_name = 'facility'
        authorization = ObjectAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering facilities by zone
        zone_id = bundle.request.GET.get('zone_id')
        if zone_id:
            facility_list = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        else:
            facility_list = Facility.objects.all()

        # call super to trigger auth
        return super(FacilityResource, self).authorized_read_list(facility_list, bundle)
        

class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        authorization = ObjectAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering groups by facility
        facility_id = bundle.request.GET.get('facility_id')
        if facility_id:
            group_list = FacilityGroup.objects.filter(facility__id=facility_id)
        else:
            group_list = FacilityGroup.objects.all()

        # call super to trigger auth
        return super(FacilityGroupResource, self).authorized_read_list(group_list, bundle)


class FacilityUserResource(ModelResource):
    """CSV Export for Test Data"""

    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'facility_user'
        authorization = ObjectAdminAuthorization()
        excludes = ['password', 'signature']
        # serializer = Serializer()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering based on zone, facility, group
        zone_id = bundle.request.GET.get('zone_id')
        facility_id = bundle.request.GET.get('facility_id')
        group_id = bundle.request.GET.get('group_id')

        # They must have a zone_id, and may have a facility_id and group_id.
        # Try to filter from most specific, to least 
        facility_user_list = []
        if group_id:
            facility_user_list = FacilityUser.objects.filter(group__id=group_id)
        elif facility_id:
            facility_user_list = FacilityUser.objects.filter(facility__id=facility_id)
        elif zone_id:
            facility_user_list = FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        else:
            raise BadRequest("Must provide a zone, facility, or group ID to sort students.")

        if not facility_user_list:
            raise NotFound("Student not found.")

        # call super to trigger auth
        return super(FacilityUserResource, self).authorized_read_list(facility_user_list, bundle)



# Normal page load if the GET request has no data
    # context = control_panel_context(request, zone_id=zone_id)
    # # check as explicitly as possible whether or not the form has been submitted 
    # if not request.GET or not(request.GET.get("facility_id") and request.GET.get("group_id")):
    #     return context
    # # Form submitted 
    # else:
    #     # Get the params 
    #     facility_id = request.GET.get("facility_id")
    #     group_id = request.GET.get("group_id")

    #     # If we error, pass this to the JS to reset the form nicely
    #     context.update({
    #         "facility_id": facility_id,
    #         "group_id": group_id,
    #     })

    #     ## CSV File Specification
    #     # CSV Cols Facility Name | Facility ID* | Group Name | Group ID | Student User ID* | Test ID | Num correct | Total number completed
        
    #     ## Fetch data for CSV
    #     # Facilities 
    #     if facility_id == 'all':
    #         # TODO(dylan): can this ever break? Will an admin always have at least one facility in a zone?
    #         facilities = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
    #     else:   
    #         facilities = Facility.objects.filter(id=facility_id)

    #     # Facility Users 
    #     if group_id == 'all': # get all students at the facility
    #         facility_ids = [facility.id for facility in facilities]
    #         facility_users = FacilityUser.objects.filter(facility__id__in=facility_ids)
    #     else: # get the students for the specific group
    #         facility_users = FacilityUser.objects.filter(group__id=group_id)
        
    #     ## A bit of error checking 
    #     if len(facility_users) == 0:
    #         messages.error(request, _("No students exist for this facility and group combination."))
    #         return context 

    #     # TestLogs
    #     user_ids = [u.id for u in facility_users]
    #     test_logs = TestLog.objects.filter(user__id__in=user_ids)

    #     if len(test_logs) == 0:
    #         messages.error(request, _("No test logs exist for these students."))
    #         return context 

    #     ## Build CSV 
    #     # Nice filename for Sarojini
    #     filename = 'f_all__' if facility_id == 'all' else 'f_%s__' % facilities[0].name
    #     filename += 'g_all__' if group_id == 'all' else 'g_%s__' % facility_users[0].group.name
    #     filename += '%s' % datetime.datetime.today().strftime("%Y-%m-%d")
    #     csv_response = HttpResponse(content_type="text/csv")
    #     csv_response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename

    #     # CSV header
    #     writer = csv.writer(csv_response)
    #     writer.writerow(["Facility Name", "Facility ID", "Group Name", "Group ID", "Student User ID", "Test ID", "Num correct", "Total number completed"])
        
    #     # CSV Body
    #     for t in test_logs:
    #         group_name = t.user.group.name if hasattr(t.user.group, "name") else UNGROUPED
    #         group_id = t.user.group.id if hasattr(t.user.group, "id") else "None"
    #         writer.writerow([t.user.facility.name, t.user.facility.id, group_name, group_id, t.user.id, t.test, t.total_correct, t.total_number])

    #     return csv_response