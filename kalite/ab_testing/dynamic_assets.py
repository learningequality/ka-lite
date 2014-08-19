from .data.groups import CONDITION_BY_FACILITY_AND_UNIT as CONDITION
from .data.conditions import CONDITION_SETTINGS


# modify ds in-place. Use when you're modifying ds rather than defining new dynamic settings
def modify_dynamic_settings(request, ds):

    user = request.session.get('facility_user')

    if user:

        # determine the facility and unit for the current user
        facility = user.facility
        unit = request.GET.get("unit", 1) # TODO-BLOCKER(jamalex): have this pull from actual unit settings

        # look up what condition the user is currently assigned to
        condition = CONDITION.get(facility.id, CONDITION.get(facility.name, CONDITION.get(facility.id[0:8], {}))).get(str(unit), "")

        # load the settings associated with the user's current condition
        new_settings = CONDITION_SETTINGS.get(condition, {})

        # merge the settings into the distributed settings (ds) object
        for key, value in new_settings.items():
            namespace, setting = key.split(".")
            if namespace not in ds:
                raise Exception("Could not modify setting '%s': the '%s' app has not defined a dynamic_assets.py file containing DynamicSettings." % (key, namespace))
            if not hasattr(ds[namespace], setting):
                raise Exception("Could not modify setting '%s': no such setting defined in the '%s' app's DynamicSettings." % (key, namespace))
            setattr(ds[namespace], setting, value)
