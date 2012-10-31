from django.db import models
from securesync.models import Zone

class Organization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    url = models.URLField(verbose_name="Website URL", blank=True)

    def get_zones(self):
        return Zone.objects.filter(pk__in=[zo.zone.pk for zo in self.zoneorganization_set.all()])

    def __unicode__(self):
        return self.name

class ZoneOrganization(models.Model):
    zone = models.ForeignKey(Zone)
    organization = models.ForeignKey(Organization)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return "Zone: %s, Organization: %s" % (self.zone, self.organization)


class OrganizationUser(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)

    def get_zones(self):
        return self.organization.get_zones()

    def __unicode__(self):
        return "%s (Organization: %s)" % (self.user, self.organization)
