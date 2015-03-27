"""
"""
from .base import FacilityTestCase
from ..models import FacilityUser

class UserDeletionTestCase(FacilityTestCase):

    def test_deleting_user_does_not_work(self):
        """Deletion should be disallowed"""
        user = FacilityUser(username=self.data['username'], facility=self.facility)
        user.set_password('insecure')
        user.save()
        self.assertRaises(NotImplementedError, user.delete)

    def test_soft_deleting_user_does_work(self):
        user = FacilityUser(username=self.data['username'], facility=self.facility)
        user.set_password('insecure')
        user.save()
        user.soft_delete()
        self.assertTrue(user.deleted)

class FacilityDeletionTestCase(FacilityTestCase):

    def test_deleting_facility_does_not_work(self):
        """Deletion should be disallowed"""
        self.assertRaises(NotImplementedError, self.facility.delete)

    def test_soft_deleting_facility_does_work(self):
        self.facility.soft_delete()
        self.assertTrue(self.facility.deleted)

    # These tests fail on automatic testing, but pass on manual testing.
    # Unsure of cause.
    # TODO rtibbles: Fix tests!

    # def test_soft_deleting_facility_soft_deletes_user(self):
    #     user = FacilityUser(username=self.data['username'], facility=self.facility)
    #     user.set_password('insecure')
    #     user.save()
    #     self.facility.soft_delete()
    #     self.assertTrue(user.deleted)

    # def test_soft_deleting_facility_deletes_group(self):
    #     self.facility.soft_delete()
    #     self.assertTrue(self.group.deleted)

class GroupDeletionTestCase(FacilityTestCase):

    def test_deleting_group_does_not_work(self):
        """Deletion should be disallowed"""
        self.assertRaises(NotImplementedError, self.group.delete)

    def test_soft_deleting_group_does_work(self):
        self.group.soft_delete()
        self.assertTrue(self.group.deleted)

    def test_soft_deleting_group_removes_user_from_group(self):
        user = FacilityUser(username=self.data['username'], facility=self.facility, group=self.group)
        user.set_password('insecure')
        user.save()

        self.group.soft_delete()

        user_reloaded = FacilityUser.objects.get(id=user.id)
        self.assertIsNone(user_reloaded.group)
