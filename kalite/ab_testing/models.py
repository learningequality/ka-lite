from django.db import models

from kalite.facility.models import FacilityUser


class FacilityUserSpecificSetting(models.Model):
    user = models.ForeignKey(FacilityUser, related_name='dynamic_settings')

    turn_off_motivational_features = models.BooleanField()
