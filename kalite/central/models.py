from django.db import models
from securesync.models import Zone
from django.contrib.auth.models import User

class Organization(models.Model):
    name = models.CharField(verbose_name="org name", max_length=100)
    description = models.TextField(help_text="<br/>How is this organization using KA Lite?", blank=True, )
    url = models.URLField(verbose_name="org URL", help_text="<br/>(optional)", blank=True)
    number = models.CharField(verbose_name="phone", max_length=100, blank=True)
    address = models.TextField(max_length=200, help_text="<br/>Street Address or PO Box, City/Town/Province, Postal Code", blank=True)
    country = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(User)
    zones = models.ManyToManyField(Zone)
    owner = models.ForeignKey(User, related_name="owned_organizations")

    def get_zones(self):
        return list(self.zones.all())

    def __unicode__(self):
        return self.name

    def save(self, owner=None, *args, **kwargs):
        if not self.owner:
            self.owner = owner
        super(Organization, self).save(*args, **kwargs)

class UserProfile(models.Model):  
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        return list(self.user.organization_set.all())

# class ZoneOrganization(models.Model):
#     zone = models.ForeignKey(Zone)
#     organization = models.ForeignKey(Organization)
#     notes = models.TextField(blank=True)

#     def __unicode__(self):
#         return "Zone: %s, Organization: %s" % (self.zone, self.organization)


# class OrganizationUser(models.Model):
#     user = models.ForeignKey(User)
#     organization = models.ForeignKey(Organization)

#     def get_zones(self):
#         return self.organization.get_zones()

#     def __unicode__(self):
#         return "%s (Organization: %s)" % (self.user, self.organization)
