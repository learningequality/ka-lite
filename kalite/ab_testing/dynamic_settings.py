from .models import FacilityUserSpecificSetting


# modify ds in-place. Use when you're modifying ds rather
# than defining new dynamic settings
def provision_dynamic_settings(ds, request, **otherinfo):
    try:
        user = request.session.get('facility_user')
        if user:
            settings = FacilityUserSpecificSetting.objects.get(user=user)
        else:
            return
    except FacilityUserSpecificSetting.DoesNotExist:
        pass
    else:
        ds.distributed.turn_off_motivational_features = settings.turn_off_motivational_features
